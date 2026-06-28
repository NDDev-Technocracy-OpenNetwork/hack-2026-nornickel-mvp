from __future__ import annotations

from typing import Protocol

from nornikel_kg.domain.ledger import EvidenceLedgerPacket
from nornikel_kg.domain.models import EvidenceSpan, SourceIngestResponse, SourceSummary


class EvidenceLedgerPort(Protocol):
    def load_demo_packet(self) -> EvidenceLedgerPacket:
        """Return the currently indexed evidence packet."""

    def list_sources(self) -> list[SourceSummary]:
        """Return registered source summaries."""

    def list_evidence_spans(self, source_id: str | None = None) -> list[EvidenceSpan]:
        """Return evidence spans, optionally scoped to one source."""

    def ingest_source_bytes(
        self,
        *,
        filename: str,
        content: bytes,
        title: str | None = None,
    ) -> SourceIngestResponse:
        """Register a CSV or Markdown-like source and extract first-class evidence."""
