from __future__ import annotations

from dataclasses import dataclass

from nornikel_kg.domain.models import EffectClaim, EvidenceSpan, PropertyMeasurement


@dataclass(frozen=True)
class EvidenceLedgerPacket:
    evidence: list[EvidenceSpan]
    measurement: PropertyMeasurement
    effect: EffectClaim
    source_title: str
