from __future__ import annotations

from typing import Protocol

from nornikel_kg.domain.ledger import EvidenceLedgerPacket


class EvidenceLedgerPort(Protocol):
    def load_demo_packet(self) -> EvidenceLedgerPacket:
        """Return the evidence packet used by the current P0 demo question."""
