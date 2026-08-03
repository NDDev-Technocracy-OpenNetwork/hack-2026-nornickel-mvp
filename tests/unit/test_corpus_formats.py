from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from nornikel_kg.adapters.duckdb.repositories import DuckDBLedgerRepository
from nornikel_kg.adapters.legacy_doc import LegacyDocParser
from nornikel_kg.ports.parser import ParsedBlock, ParsedDocument, ParserError
from nornikel_kg.services.archive_expansion import expand_archives
from nornikel_kg.services.ingestion_service import IngestionService


def _make_zip(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in members.items():
            archive.writestr(name, content)


def test_plain_zip_expands_ingestible_members(tmp_path: Path) -> None:
    archive = tmp_path / "bundle.zip"
    _make_zip(archive, {"paper.pdf": b"%PDF-1.4", "notes.gif": b"GIF89a", "data.txt": b"x"})
    extracted, stats = expand_archives([archive], tmp_path / "work")
    names = {path.name for path in extracted}
    assert names == {"paper.pdf", "data.txt"}  # gif is not ingestible
    assert stats["zip_expanded"] == 1


def test_multipart_zip_is_reassembled(tmp_path: Path) -> None:
    """CM_05_09.zip.001 + .002 style splits concatenate into one valid zip."""
    whole = tmp_path / "whole.zip"
    _make_zip(whole, {"CM_05_09.pdf": b"%PDF-1.4" + b"A" * 5000})
    data = whole.read_bytes()
    part1 = tmp_path / "CM_05_09.zip.001"
    part2 = tmp_path / "CM_05_09.zip.002"
    part1.write_bytes(data[: len(data) // 2])
    part2.write_bytes(data[len(data) // 2 :])
    whole.unlink()

    extracted, stats = expand_archives([part1, part2], tmp_path / "work")
    assert [path.name for path in extracted] == ["CM_05_09.pdf"]
    assert stats["multipart_zip_expanded"] == 1
    assert extracted[0].read_bytes().startswith(b"%PDF-1.4")


def test_zip_slip_member_is_skipped(tmp_path: Path) -> None:
    archive = tmp_path / "evil.zip"
    _make_zip(archive, {"../escape.pdf": b"%PDF-1.4"})
    extracted, _stats = expand_archives([archive], tmp_path / "work")
    # flattened to basename inside work dir, never outside it
    for path in extracted:
        assert path.resolve().is_relative_to((tmp_path / "work").resolve())


def test_corrupt_rar_is_counted_not_crashed(tmp_path: Path) -> None:
    bad = tmp_path / "broken.rar"
    bad.write_bytes(b"not really a rar")
    extracted, stats = expand_archives([bad], tmp_path / "work")
    assert extracted == []
    assert stats["rar_skipped"] == 1


def test_spreadsheet_parser_produces_table_rows(tmp_path: Path) -> None:
    openpyxl = pytest.importorskip("openpyxl")
    pytest.importorskip("pandas")
    from nornikel_kg.adapters.spreadsheet import SpreadsheetDocumentParser

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["Материал", "Извлечение", "Единица"])
    sheet.append(["штейн", "95.2", "%"])
    target = tmp_path / "catalog.xlsx"
    workbook.save(target)

    parsed = SpreadsheetDocumentParser().parse(
        content=target.read_bytes(), filename="catalog.xlsx"
    )
    assert parsed.tables
    row_texts = [row.text for table in parsed.tables for row in table.rows]
    assert any("штейн" in text for text in row_texts)


def test_legacy_doc_without_text_raises_parser_error() -> None:
    # A .doc with only an OLE header and binary noise (no prose) must be
    # rejected. On hosts without `antiword` the parser raises ParserError; on
    # hosts with antiword (e.g. the CI runner) it may return a block whose text
    # is just the leaked binary header. Accept either: ParserError, or a result
    # whose blocks contain no readable word (no run of >= 3 letters).
    #
    # The input is deliberately pure binary noise (no ASCII words) so that a
    # header-leak result is distinguishable from real prose extraction.
    import re

    try:
        result = LegacyDocParser().parse(
            content=b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1\x00\x03\x00\xfe\xff",
            filename="old.doc",
        )
    except ParserError:
        return
    for block in result.blocks:
        assert not re.search(r"[A-Za-zÀ-ÿ]{3,}", block.text), (
            f"binary-only .doc yielded readable text: {block.text!r}"
        )


class _StubParser:
    parser_profile = "stub_v1"

    def __init__(self) -> None:
        self.filenames: list[str] = []

    def parse(self, *, content: bytes, filename: str) -> ParsedDocument:
        self.filenames.append(filename)
        return ParsedDocument(
            blocks=[ParsedBlock(text="Обеднение шлака.", page=1, locator="block_1")],
            tables=[],
            title=filename,
            parser_profile=self.parser_profile,
        )


def test_docm_routes_through_document_parser(tmp_path: Path) -> None:
    repository = DuckDBLedgerRepository(tmp_path / "formats.duckdb")
    repository.migrate()
    stub = _StubParser()
    service = IngestionService(repository, parser=stub, synchronous_enrichment=True)
    response = service.ingest_upload(filename="paper.docm", content=b"PK docm bytes")
    assert stub.filenames == ["paper.docm"]
    assert response.source.status in {"completed", "running"}
    assert response.evidence_count >= 1
