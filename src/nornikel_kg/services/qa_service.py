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
    """Deterministic evidence-led QA over the current DuckDB ledger packet."""

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
        allowed_evidence = self.source_label_policy.filter_spans(packet.evidence)
        allowed_span_ids = {span.span_id for span in allowed_evidence}
        selected_experiments = self._select_experiments(
            question=request.question,
            experiments=packet.experiments,
            request_filters=request.filters,
        )
        selected_experiments = [
            experiment
            for experiment in selected_experiments
            if any(span_id in allowed_span_ids for span_id in experiment.evidence_ids)
        ]
        selected_evidence = self._evidence_for_experiments(allowed_evidence, selected_experiments)
        graph_paths = [
            self._graph_path_for_experiment(experiment, selected_evidence)
            for experiment in selected_experiments
        ]
        summary = [
            self._answer_sentence_for_experiment(experiment, graph_paths[index])
            for index, experiment in enumerate(selected_experiments)
        ]
        verification = self.claim_verifier.verify(
            answer_summary=summary,
            evidence_spans=selected_evidence,
            source_label_policy=self.source_label_policy,
        )
        conflicts = self._conflicts_for_question(request.question, packet.conflicts)
        gaps = self._gaps_for_question(
            question=request.question,
            packet_gaps=packet.gaps,
            selected_experiments=selected_experiments,
        )
        return AskResponse(
            run_id=f"qa_run_{stable_hash([request.question, request.language], 12)}",
            answer_summary=summary,
            confidence="high" if selected_experiments else "low",
            experiments=selected_experiments,
            evidence=selected_evidence,
            graph_paths=graph_paths if request.include_graph else [],
            verification=verification,
            conflicts=conflicts,
            gaps=gaps if request.include_gaps else [],
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
        experiment = ExperimentRow(
            source_id=primary_span.source_id,
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
        return EvidenceLedgerPacket(
            evidence=evidence,
            measurements=[measurement],
            effects=[effect],
            experiments=[experiment],
            source_titles={primary_span.source_id: "Synthetic Ni-Cu aging report"},
            conflicts=[
                {
                    "conflict_group_id": "conf_nicu_hardness_method",
                    "type": "method_mismatch",
                    "summary": (
                        "Похожий режим в соседнем источнике измерен другим методом, "
                        "поэтому не сравнивается напрямую с HV."
                    ),
                    "supporting_span_ids": [evidence[1].span_id],
                }
            ],
            gaps=[
                {
                    "gap_id": "gap_nicu_conductivity_aging_700c",
                    "type": "missing_measurement",
                    "description": (
                        "Для Ni-Cu после старения 700 C / 8 ч нет валидированного "
                        "измерения электропроводности в доступном ledger."
                    ),
                    "near_miss_evidence_span_ids": [primary_span.span_id],
                }
            ],
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

    def _select_experiments(
        self,
        *,
        question: str,
        experiments: list[ExperimentRow],
        request_filters: dict[str, object] | None = None,
    ) -> list[ExperimentRow]:
        normalized_question = self._normalize(question)
        requested_property = self._requested_property(question)
        has_request_filters = bool(request_filters)
        exact_materials = {
            self._normalize(experiment.material_name)
            for experiment in experiments
            if self._normalize(experiment.material_name) in normalized_question
        }
        filtered_experiments: list[ExperimentRow] = []
        scored: list[tuple[int, ExperimentRow]] = []
        for experiment in experiments:
            if not self._matches_filters(experiment, request_filters):
                continue
            filtered_experiments.append(experiment)
            if exact_materials and self._normalize(experiment.material_name) not in exact_materials:
                continue
            if requested_property and not self._property_matches(requested_property, experiment):
                continue
            score = self._score_experiment(question, experiment)
            if score > 0:
                scored.append((score, experiment))
        if not scored and not requested_property:
            if has_request_filters:
                return filtered_experiments[:5]
            return experiments[:5]
        scored.sort(key=lambda item: (-item[0], item[1].experiment_id))
        return [experiment for _, experiment in scored[:5]]

    def _matches_filters(
        self,
        experiment: ExperimentRow,
        filters: dict[str, object] | None,
    ) -> bool:
        if not filters:
            return True
        source_filter = self._list_filter_values(filters, "source_ids", "source_id")
        if source_filter and not self._matches_source_filter(experiment.source_id, source_filter):
            return False
        material_filter = self._text_filter_values(filters, "material_name", "material")
        if material_filter and not self._matches_text_filter(
            experiment.material_name, material_filter
        ):
            return False
        property_filter = self._text_filter_values(filters, "property_name", "property")
        if property_filter and not self._matches_text_filter(
            experiment.property_name, property_filter
        ):
            return False
        regime_filter = self._text_filter_values(filters, "regime_summary", "regime")
        if regime_filter and not self._matches_text_filter(
            experiment.regime_summary, regime_filter
        ):
            return False
        experiment_filter = self._text_filter_values(filters, "experiment_id")
        if experiment_filter and not self._matches_text_filter(
            experiment.experiment_id, experiment_filter
        ):
            return False
        regime_id_filter = self._text_filter_values(filters, "regime_id")
        if not regime_id_filter:
            return True
        return self._matches_text_filter(experiment.regime_id, regime_id_filter)

    def _matches_source_filter(self, source_id: str | None, allowed_source_ids: set[str]) -> bool:
        if not allowed_source_ids:
            return True
        return source_id is not None and source_id in allowed_source_ids

    def _list_filter_values(self, filters: dict[str, object], *keys: str) -> set[str]:
        for key in keys:
            raw = filters.get(key)
            if raw is None:
                continue
            if isinstance(raw, str):
                value = raw.strip()
                return {value} if value else set()
            if isinstance(raw, list | tuple):
                return {
                    str(item).strip()
                    for item in raw
                    if str(item).strip()
                }
        return set()

    def _text_filter_values(self, filters: dict[str, object], *keys: str) -> set[str]:
        for key in keys:
            raw = filters.get(key)
            if raw is None:
                continue
            if isinstance(raw, str):
                normalized = self._normalize(raw.strip())
                return {normalized} if normalized else set()
            if isinstance(raw, list | tuple):
                normalized_values = {
                    self._normalize(str(item).strip())
                    for item in raw
                    if str(item).strip()
                }
                return {value for value in normalized_values if value}
        return set()

    def _matches_text_filter(self, value: str, candidates: set[str]) -> bool:
        if not candidates:
            return True
        normalized_value = self._normalize(value)
        return any(candidate in normalized_value for candidate in candidates)

    def _score_experiment(self, question: str, experiment: ExperimentRow) -> int:
        normalized_question = self._normalize(question)
        score = 0
        material = self._normalize(experiment.material_name)
        if material and material in normalized_question:
            score += 6
        elif self._mentions_nicu_family(normalized_question) and self._is_nicu_family(experiment):
            score += 4
        if self._property_matches("hardness", experiment) and (
            "hardness" in normalized_question or "тверд" in normalized_question
        ):
            score += 5
        if self._regime_matches(normalized_question, experiment):
            score += 4
        if "700" in normalized_question and "700" in experiment.regime_summary:
            score += 1
        if (
            "8" in normalized_question or "8h" in normalized_question
        ) and "8" in experiment.regime_summary:
            score += 1
        return score

    def _requested_property(self, question: str) -> str | None:
        normalized_question = self._normalize(question)
        if "электропровод" in normalized_question or "conductivity" in normalized_question:
            return "conductivity"
        if "vickers" in normalized_question or "виккер" in normalized_question:
            return "vickers_hardness"
        if "rockwell" in normalized_question or "роквел" in normalized_question:
            return "rockwell_hardness"
        if "hardness" in normalized_question or "тверд" in normalized_question:
            return "hardness"
        return None

    def _property_matches(self, requested_property: str, experiment: ExperimentRow) -> bool:
        property_id = experiment.property_id.lower()
        property_name = experiment.property_name.lower()
        if requested_property == "hardness":
            return "hardness" in property_id or "тверд" in property_name
        if requested_property == "conductivity":
            return "conductivity" in property_id or "электропровод" in property_name
        return requested_property in property_id

    def _regime_matches(self, normalized_question: str, experiment: ExperimentRow) -> bool:
        regime = self._normalize(experiment.regime_summary)
        if ("старен" in normalized_question or "aging" in normalized_question) and (
            "старен" in regime or "aging" in regime
        ):
            return True
        return ("отжиг" in normalized_question or "anneal" in normalized_question) and (
            "отжиг" in regime or "anneal" in regime
        )

    def _evidence_for_experiments(
        self,
        evidence: list[EvidenceSpan],
        experiments: list[ExperimentRow],
    ) -> list[EvidenceSpan]:
        requested_span_ids = {
            span_id
            for experiment in experiments
            for span_id in experiment.evidence_ids
        }
        return [span for span in evidence if span.span_id in requested_span_ids]

    def _graph_path_for_experiment(
        self,
        experiment: ExperimentRow,
        evidence: list[EvidenceSpan],
    ) -> GraphPath:
        primary_span = next(span for span in evidence if span.span_id in experiment.evidence_ids)
        measurement_id = f"meas:{experiment.experiment_id}:{experiment.property_id}"
        return GraphPath(
            path_id=f"path_{stable_hash([experiment.experiment_id, experiment.property_id], 10)}",
            nodes=[
                experiment.material_id,
                experiment.experiment_id,
                experiment.regime_id,
                f"step_{experiment.regime_id}",
                measurement_id,
                experiment.property_id,
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

    def _answer_sentence_for_experiment(
        self,
        experiment: ExperimentRow,
        graph_path: GraphPath,
    ) -> AnswerSentence:
        value = experiment.measurement.get("value")
        unit = experiment.measurement.get("unit")
        delta = experiment.measurement.get("delta_value")
        delta_unit = experiment.measurement.get("delta_unit")
        direction = experiment.measurement.get("effect_direction")
        value_text = self._format_value(value, unit)
        delta_text = "" if delta is None else f", Δ {self._format_value(delta, delta_unit)}"
        sentence = (
            f"{experiment.material_name}: {experiment.regime_summary} дал эффект "
            f"{direction} по свойству {experiment.property_name}: {value_text}{delta_text}."
        )
        return AnswerSentence(
            sentence=sentence,
            supporting_span_ids=experiment.evidence_ids,
            supporting_fact_ids=[f"fact:{experiment.experiment_id}:{experiment.property_id}"],
            graph_path_ids=[graph_path.path_id],
        )

    def _conflicts_for_question(
        self,
        question: str,
        conflicts: list[dict[str, object]],
    ) -> list[dict[str, object]]:
        normalized_question = self._normalize(question)
        if "противор" in normalized_question or "conflict" in normalized_question:
            return conflicts
        if "method" in normalized_question or "метод" in normalized_question:
            return conflicts
        return conflicts[:1]

    def _gaps_for_question(
        self,
        *,
        question: str,
        packet_gaps: list[dict[str, object]],
        selected_experiments: list[ExperimentRow],
    ) -> list[dict[str, object]]:
        requested_property = self._requested_property(question)
        if not selected_experiments or requested_property == "conductivity":
            return packet_gaps
        return []

    def _normalize(self, value: str) -> str:
        return value.lower().replace("ё", "е").replace("-", "")

    def _format_value(self, value: object, unit: object) -> str:
        value_text = f"{value:g}" if isinstance(value, int | float) else str(value)
        return f"{value_text} {unit}".strip()

    def _mentions_nicu_family(self, normalized_question: str) -> bool:
        return "nicu" in normalized_question or "cuni" in normalized_question or (
            "ni" in normalized_question and "cu" in normalized_question
        )

    def _is_nicu_family(self, experiment: ExperimentRow) -> bool:
        material = self._normalize(experiment.material_name)
        return "ni" in material and "cu" in material
