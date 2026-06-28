from __future__ import annotations

from nornikel_kg.domain.answer_claims import ClaimVerifier
from nornikel_kg.domain.evidence import EvidenceSpanFactory
from nornikel_kg.domain.ids import claim_id, fact_id, source_id_from_bytes, stable_hash
from nornikel_kg.domain.ledger import EvidenceLedgerPacket
from nornikel_kg.domain.models import (
    AnswerSentence,
    AskRequest,
    AskResponse,
    EffectClaim,
    EvidenceSpan,
    ExperimentRow,
    GraphPath,
    PropertyMeasurement,
)
from nornikel_kg.domain.security import SourceLabelPolicy
from nornikel_kg.ports.ledger import EvidenceLedgerPort


class DemoQAService:
    """Deterministic evidence packet used until ingestion/retrieval adapters are wired."""

    def __init__(
        self,
        *,
        evidence_factory: EvidenceSpanFactory | None = None,
        claim_verifier: ClaimVerifier | None = None,
        source_label_policy: SourceLabelPolicy | None = None,
        ledger_repository: EvidenceLedgerPort | None = None,
    ) -> None:
        self.evidence_factory = evidence_factory or EvidenceSpanFactory()
        self.claim_verifier = claim_verifier or ClaimVerifier()
        self.source_label_policy = source_label_policy or SourceLabelPolicy()
        self.ledger_repository = ledger_repository

    def ask(self, request: AskRequest) -> AskResponse:
        packet = self._load_packet()
        evidence = packet.evidence
        allowed_evidence = self.source_label_policy.filter_spans(evidence)
        primary_span = allowed_evidence[0]
        measurement = packet.measurement
        effect = packet.effect
        graph_path = GraphPath(
            path_id="path_nicu_aging_hardness",
            nodes=[
                "mat_nicu_30",
                measurement.experiment_id,
                effect.regime_id,
                "step_aging_700c_8h",
                measurement.measurement_id,
                measurement.property_id,
                primary_span.span_id,
                primary_span.source_id,
            ],
            relationships=[
                "USED_IN_EXPERIMENT",
                "APPLIES_REGIME",
                "HAS_STEP",
                "HAS_MEASUREMENT",
                "OF_PROPERTY",
                "SUPPORTED_BY",
                "FROM_DOCUMENT",
            ],
        )
        summary = [
            AnswerSentence(
                sentence=(
                    "Для синтетического примера Ni-30Cu старение при 700 C в течение 8 ч "
                    "повысило твердость до 245 HV, что на 35 HV выше исходного состояния."
                ),
                supporting_span_ids=[primary_span.span_id],
                supporting_fact_ids=[measurement.measurement_id, effect.effect_id],
                graph_path_ids=[graph_path.path_id],
            )
        ]
        verification = self.claim_verifier.verify(
            answer_summary=summary,
            evidence_spans=allowed_evidence,
            source_label_policy=self.source_label_policy,
        )
        return AskResponse(
            run_id=f"qa_run_{stable_hash([request.question, request.language], 12)}",
            answer_summary=summary,
            confidence="high",
            experiments=[
                ExperimentRow(
                    experiment_id=measurement.experiment_id,
                    material_id=effect.material_id,
                    material_name="Ni-30Cu",
                    regime_id=effect.regime_id,
                    regime_summary="Старение, 700 C, 8 ч, воздух",
                    property_id=measurement.property_id,
                    property_name=measurement.property_name,
                    measurement={
                        "value": measurement.value,
                        "unit": measurement.unit,
                        "delta_value": effect.delta_value,
                        "delta_unit": effect.delta_unit,
                        "effect_direction": effect.direction,
                    },
                    evidence_ids=[primary_span.span_id],
                    validation_status=measurement.validation_status,
                )
            ],
            evidence=allowed_evidence,
            graph_paths=[graph_path] if request.include_graph else [],
            verification=verification,
            conflicts=[
                {
                    "conflict_group_id": "conf_nicu_hardness_method",
                    "type": "method_mismatch",
                    "summary": (
                        "Похожий режим в соседнем источнике измерен Rockwell, "
                        "поэтому не сравнивается напрямую с HV."
                    ),
                    "supporting_span_ids": [
                        span.span_id
                        for span in allowed_evidence
                        if span.span_id != primary_span.span_id
                    ],
                }
            ],
            gaps=[
                {
                    "gap_id": "gap_nicu_conductivity_aging_700c",
                    "type": "missing_measurement",
                    "description": (
                        "Для Ni-30Cu после старения 700 C / 8 ч нет измерения "
                        "электропроводности."
                    ),
                    "near_miss_evidence_span_ids": [primary_span.span_id],
                }
            ]
            if request.include_gaps
            else [],
            follow_up_queries=[
                "Показать режимы старения Ni-Cu с измеренной электропроводностью",
                "Сравнить Ni-30Cu и CuNi30 по твердости после отжига",
            ],
        )

    def _load_packet(self) -> EvidenceLedgerPacket:
        if self.ledger_repository is not None:
            return self.ledger_repository.load_demo_packet()
        return self._fallback_packet()

    def _fallback_packet(self) -> EvidenceLedgerPacket:
        evidence = self._demo_evidence()
        primary_span = evidence[0]
        measurement_id = fact_id(
            "measurement",
            {
                "experiment_id": "exp_nicu_aging_700c_8h",
                "property": "vickers_hardness",
                "value": 245,
                "unit": "HV",
            },
        )
        measurement = PropertyMeasurement(
            measurement_id=measurement_id,
            experiment_id="exp_nicu_aging_700c_8h",
            property_id="prop_vickers_hardness",
            property_name="Твердость по Виккерсу",
            value=245,
            unit="HV",
            original_value="245 HV",
            method="Vickers HV10",
            supporting_span_ids=[primary_span.span_id],
        )
        effect = EffectClaim(
            effect_id=claim_id(
                {
                    "experiment_id": measurement.experiment_id,
                    "direction": "increase",
                    "supporting_span_ids": measurement.supporting_span_ids,
                }
            ),
            experiment_id=measurement.experiment_id,
            material_id="mat_nicu_30",
            regime_id="reg_aging_700c_8h_air",
            property_id=measurement.property_id,
            direction="increase",
            baseline_measurement_id="meas_nicu_baseline_hv",
            treated_measurement_id=measurement.measurement_id,
            delta_value=35,
            delta_unit="HV",
            qualitative_summary="Старение при 700 C в течение 8 ч повысило твердость Ni-30Cu.",
            supporting_span_ids=[primary_span.span_id],
        )
        return EvidenceLedgerPacket(
            evidence=evidence,
            measurement=measurement,
            effect=effect,
            source_title="Synthetic Ni-Cu aging report",
        )

    def _demo_evidence(self) -> list[EvidenceSpan]:
        source_id = source_id_from_bytes(b"synthetic_nicu_aging_report_v1")
        table_text = (
            "Sample Ni-30Cu-A | Aging 700 C | 8 h | air | Vickers hardness HV10 | "
            "baseline 210 HV | aged 245 HV"
        )
        conflict_text = (
            "A neighboring Cu-Ni trial used Rockwell hardness after 700 C aging; "
            "method mismatch prevents direct numeric comparison."
        )
        return [
            self.evidence_factory.create(
                source_id=source_id,
                artifact_type="table",
                parser_profile="synthetic_fixture_v1",
                artifact_locator="tables/mechanical_properties.csv",
                span_type="table_row",
                visible_text=table_text,
                page=2,
                stable_locator="table_001:row_003",
                validation_status="validated_rule",
                evidence_confidence=1.0,
                security_label="internal",
            ),
            self.evidence_factory.create(
                source_id=source_id,
                artifact_type="text",
                parser_profile="synthetic_fixture_v1",
                artifact_locator="reports/nicu_aging_report.md",
                span_type="text",
                visible_text=conflict_text,
                page=3,
                stable_locator="section:discussion:block_002",
                validation_status="validated_rule",
                evidence_confidence=0.98,
                security_label="internal",
            ),
        ]
