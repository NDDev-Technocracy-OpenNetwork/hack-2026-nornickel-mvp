from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Protocol

from nornikel_kg.adapters.duckdb.repositories import DuckDBLedgerRepository, SourceIngestError
from nornikel_kg.domain.ids import source_id_from_bytes, stable_hash
from nornikel_kg.domain.models import SourceIngestResponse
from nornikel_kg.ports.parser import (
    DocumentParserPort,
    NoTextLayerError,
    ParsedBlock,
    ParsedDocument,
    ParserError,
    UrlFetcherPort,
)

logger = logging.getLogger(__name__)

PARSER_EXTENSIONS = {".pdf", ".docx"}
TEXT_EXTENSIONS = {".csv", ".md", ".markdown", ".txt", ".text"}


class ExtractionServiceProtocol(Protocol):
    def process_source(self, source_id: str) -> dict[str, int]:
        """Extract entities/relations from a source's spans."""


class IngestionService:
    """Orchestrates source ingestion: parse -> ledger writes -> run lifecycle.

    Parser failures and text-layer-absent PDFs quarantine the source (run row
    with status=quarantined, no evidence spans) instead of surfacing a 500.
    """

    def __init__(
        self,
        repository: DuckDBLedgerRepository,
        *,
        parser: DocumentParserPort | None = None,
        url_fetcher: UrlFetcherPort | None = None,
        artifact_root: Path | None = None,
        extraction_service: ExtractionServiceProtocol | None = None,
    ) -> None:
        self.repository = repository
        self._parser = parser
        self._url_fetcher = url_fetcher
        self.artifact_root = artifact_root
        self.extraction_service = extraction_service

    @property
    def parser(self) -> DocumentParserPort:
        if self._parser is None:
            from nornikel_kg.adapters.docling import DoclingDocumentParser

            self._parser = DoclingDocumentParser()
        return self._parser

    @property
    def url_fetcher(self) -> UrlFetcherPort:
        if self._url_fetcher is None:
            from nornikel_kg.adapters.trafilatura import TrafilaturaUrlFetcher

            self._url_fetcher = TrafilaturaUrlFetcher()
        return self._url_fetcher

    def ingest_upload(
        self,
        *,
        filename: str,
        content: bytes,
        title: str | None = None,
    ) -> SourceIngestResponse:
        extension = Path(filename).suffix.lower()
        if extension in TEXT_EXTENSIONS:
            response = self.repository.ingest_source_bytes(
                filename=filename, content=content, title=title
            )
            extraction_counters = self._run_extraction(response.source.source_id)
            self._record_run(
                source_id=response.source.source_id,
                status="completed",
                stage="ledger_write",
                counters={
                    "evidence_spans": response.evidence_count,
                    "measurements": response.measurement_count,
                    **extraction_counters,
                },
            )
            return self._with_run_status(response)
        if extension in PARSER_EXTENSIONS:
            return self._ingest_parsed(filename=filename, content=content, title=title)
        raise SourceIngestError(f"Unsupported upload extension: {extension}")

    def ingest_url(self, url: str) -> SourceIngestResponse:
        page = self.url_fetcher.fetch(url)
        content = page.text.encode("utf-8")
        source_id = source_id_from_bytes(content)
        parsed = ParsedDocument(
            blocks=[
                ParsedBlock(text=line.strip(), page=None, locator=f"url_block_{index:03d}")
                for index, line in enumerate(page.text.splitlines(), start=1)
                if line.strip()
            ],
            tables=[],
            title=page.title or url,
            parser_profile="trafilatura_v1",
            metadata={
                "url": url,
                **({"date": page.date} if page.date else {}),
            },
        )
        text_spans, table_spans = self.repository.ingest_parsed_document(
            source_id=source_id,
            raw_sha256=hashlib.sha256(content).hexdigest(),
            title=page.title or url,
            document_type="url",
            parsed=parsed,
            artifact_locator=url,
        )
        self._archive_artifact(source_id, "parsed.txt", content)
        extraction_counters = self._run_extraction(source_id)
        self._record_run(
            source_id=source_id,
            status="completed",
            stage="ledger_write",
            counters={"evidence_spans": text_spans + table_spans, **extraction_counters},
        )
        return self._response_for(source_id)

    def _ingest_parsed(
        self,
        *,
        filename: str,
        content: bytes,
        title: str | None,
    ) -> SourceIngestResponse:
        source_id = source_id_from_bytes(content)
        raw_sha256 = hashlib.sha256(content).hexdigest()
        document_type = Path(filename).suffix.lower().lstrip(".")
        self._record_run(source_id=source_id, status="running", stage="parse")
        try:
            parsed = self.parser.parse(content=content, filename=filename)
        except NoTextLayerError as error:
            self._quarantine(source_id, filename, raw_sha256, document_type, str(error))
            return self._response_for(source_id, warnings=[str(error)])
        except ParserError as error:
            self._quarantine(source_id, filename, raw_sha256, document_type, str(error))
            return self._response_for(source_id, warnings=[str(error)])
        except Exception as error:  # never 500 on parser crashes
            logger.exception("Unexpected parser failure for %s", filename)
            self._quarantine(source_id, filename, raw_sha256, document_type, repr(error))
            return self._response_for(source_id, warnings=[repr(error)])

        self._archive_artifact(source_id, filename, content)
        text_spans, table_spans = self.repository.ingest_parsed_document(
            source_id=source_id,
            raw_sha256=raw_sha256,
            title=title or parsed.title or filename,
            document_type=document_type,
            parsed=parsed,
            artifact_locator=filename,
        )
        extraction_counters = self._run_extraction(source_id)
        self._record_run(
            source_id=source_id,
            status="completed",
            stage="ledger_write",
            counters={
                "text_spans": text_spans,
                "table_spans": table_spans,
                **extraction_counters,
            },
        )
        return self._response_for(source_id)

    def _quarantine(
        self,
        source_id: str,
        filename: str,
        raw_sha256: str,
        document_type: str,
        error: str,
    ) -> None:
        # Register the source row so the quarantined state is visible in the UI,
        # but write no evidence spans.
        empty = ParsedDocument(blocks=[], tables=[], parser_profile="quarantined")
        self.repository.ingest_parsed_document(
            source_id=source_id,
            raw_sha256=raw_sha256,
            title=filename,
            document_type=document_type,
            parsed=empty,
            artifact_locator=filename,
        )
        self._record_run(
            source_id=source_id,
            status="quarantined",
            stage="parse",
            error=error,
        )

    def _run_extraction(self, source_id: str) -> dict[str, int]:
        """Auto-linking stage; extraction failures never fail the ingest."""
        if self.extraction_service is None:
            return {}
        try:
            return self.extraction_service.process_source(source_id)
        except Exception:
            logger.exception("Extraction failed for %s; spans are still ingested", source_id)
            return {}

    def _record_run(
        self,
        *,
        source_id: str,
        status: str,
        stage: str,
        error: str | None = None,
        counters: dict[str, int] | None = None,
    ) -> None:
        run_id = f"ing_{stable_hash([source_id], 16)}"
        self.repository.record_ingestion_run(
            run_id=run_id,
            source_id=source_id,
            status=status,
            stage=stage,
            error=error,
            counters=counters,
        )

    def _archive_artifact(self, source_id: str, filename: str, content: bytes) -> None:
        if self.artifact_root is None:
            return
        try:
            target_dir = self.artifact_root / "sources" / source_id
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / filename).write_bytes(content)
        except OSError:  # artifact archive is best-effort, never blocks ingest
            logger.warning("Could not archive artifact for %s", source_id, exc_info=True)

    def _response_for(
        self, source_id: str, warnings: list[str] | None = None
    ) -> SourceIngestResponse:
        source = self.repository.get_source(source_id)
        if source is None:
            raise SourceIngestError(f"Source {source_id} was not registered.")
        statuses = self.repository.latest_run_statuses()
        summary = source.model_copy(update={"status": statuses.get(source_id, source.status)})
        return SourceIngestResponse(
            source=summary,
            evidence_count=summary.evidence_count,
            measurement_count=summary.measurement_count,
            warnings=warnings or [],
        )

    def _with_run_status(self, response: SourceIngestResponse) -> SourceIngestResponse:
        statuses = self.repository.latest_run_statuses()
        status = statuses.get(response.source.source_id)
        if status is None:
            return response
        return response.model_copy(
            update={"source": response.source.model_copy(update={"status": status})}
        )
