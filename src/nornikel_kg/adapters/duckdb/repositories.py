from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import duckdb
from nornikel_kg.domain.evidence import EvidenceSpanFactory
from nornikel_kg.domain.ids import claim_id, fact_id, source_id_from_bytes
from nornikel_kg.domain.ledger import EvidenceLedgerPacket
from nornikel_kg.domain.models import EffectClaim, EvidenceSpan, PropertyMeasurement


class DuckDBLedgerRepository:
    def __init__(self, db_path: Path, *, migrations_dir: Path | None = None) -> None:
        self.db_path = db_path
        self.migrations_dir = migrations_dir or Path(__file__).resolve().parent / "migrations"
        self.evidence_factory = EvidenceSpanFactory()

    def migrate(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(str(self.db_path)) as connection:
            for migration_path in sorted(self.migrations_dir.glob("*.sql")):
                connection.execute(migration_path.read_text(encoding="utf-8"))

    def seed_synthetic_fixture(self, sample_dir: Path) -> EvidenceLedgerPacket:
        self.migrate()
        csv_path = sample_dir / "mechanical_properties.csv"
        report_path = sample_dir / "nicu_aging_report.md"
        csv_bytes = csv_path.read_bytes()
        report_bytes = report_path.read_bytes()
        source_id = source_id_from_bytes(report_bytes + b"\n---\n" + csv_bytes)
        raw_sha256 = hashlib.sha256(report_bytes + csv_bytes).hexdigest()

        table_span, conflict_span = self._build_synthetic_spans(
            source_id=source_id,
            csv_path=csv_path,
            report_path=report_path,
        )
        measurement = self._build_measurement(table_span)
        effect = self._build_effect(measurement, table_span)

        with duckdb.connect(str(self.db_path)) as connection:
            connection.execute("DELETE FROM sources WHERE source_id = ?", [source_id])
            connection.execute("DELETE FROM evidence_spans WHERE source_id = ?", [source_id])
            connection.execute(
                "DELETE FROM property_measurements WHERE measurement_id = ?",
                [measurement.measurement_id],
            )
            connection.execute("DELETE FROM effect_claims WHERE effect_id = ?", [effect.effect_id])
            connection.execute(
                """
                INSERT INTO sources (source_id, title, raw_sha256, security_label)
                VALUES (?, ?, ?, ?)
                """,
                [source_id, "Synthetic Ni-Cu aging report", raw_sha256, "internal"],
            )
            self._insert_evidence_span(connection, table_span)
            self._insert_evidence_span(connection, conflict_span)
            self._insert_measurement(connection, measurement)
            self._insert_effect(connection, effect)

        return self.load_demo_packet()

    def load_demo_packet(self) -> EvidenceLedgerPacket:
        with duckdb.connect(str(self.db_path)) as connection:
            source_row = connection.execute(
                """
                SELECT source_id, title
                FROM sources
                WHERE title = 'Synthetic Ni-Cu aging report'
                ORDER BY created_at DESC
                LIMIT 1
                """
            ).fetchone()
            if source_row is None:
                raise LookupError("Synthetic evidence ledger is empty. Seed fixtures first.")

            evidence_rows = connection.execute(
                """
                SELECT
                  span_id,
                  source_id,
                  artifact_id,
                  span_type,
                  visible_text,
                  page,
                  locator_json,
                  validation_status,
                  evidence_confidence,
                  security_label
                FROM evidence_spans
                WHERE source_id = ?
                ORDER BY page NULLS LAST, span_type DESC
                """,
                [source_row[0]],
            ).fetchall()
            evidence = [self._evidence_from_row(row) for row in evidence_rows]
            measurement_row = connection.execute(
                """
                SELECT
                  measurement_id,
                  experiment_id,
                  property_id,
                  property_name,
                  value,
                  unit,
                  original_value,
                  method,
                  supporting_span_ids_json,
                  validation_status
                FROM property_measurements
                ORDER BY measurement_id
                LIMIT 1
                """
            ).fetchone()
            effect_row = connection.execute(
                """
                SELECT
                  effect_id,
                  experiment_id,
                  material_id,
                  regime_id,
                  property_id,
                  direction,
                  supporting_span_ids_json,
                  baseline_measurement_id,
                  treated_measurement_id,
                  delta_value,
                  delta_unit,
                  qualitative_only,
                  qualitative_summary
                FROM effect_claims
                ORDER BY effect_id
                LIMIT 1
                """
            ).fetchone()
            if measurement_row is None or effect_row is None:
                raise LookupError("Synthetic evidence ledger is missing facts.")

        return EvidenceLedgerPacket(
            evidence=evidence,
            measurement=self._measurement_from_row(measurement_row),
            effect=self._effect_from_row(effect_row),
            source_title=str(source_row[1]),
        )

    def list_sources(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []
        with duckdb.connect(str(self.db_path)) as connection:
            rows = connection.execute(
                """
                SELECT source_id, title, security_label
                FROM sources
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            {
                "source_id": str(row[0]),
                "title": str(row[1]),
                "document_type": "report",
                "security_label": str(row[2]),
                "status": "ledger",
            }
            for row in rows
        ]

    def _build_synthetic_spans(
        self,
        *,
        source_id: str,
        csv_path: Path,
        report_path: Path,
    ) -> tuple[EvidenceSpan, EvidenceSpan]:
        with csv_path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        primary = rows[0]
        table_text = (
            f"Sample {primary['material']}-A | Aging {primary['temperature_c']} C | "
            f"{primary['duration_h']} h | {primary['atmosphere']} | "
            f"{primary['property']} {primary['method']} | "
            f"baseline {primary['baseline_value']} {primary['unit']} | "
            f"aged {primary['treated_value']} {primary['unit']}"
        )
        report_text = report_path.read_text(encoding="utf-8")
        conflict_text = next(
            line.strip()
            for line in report_text.splitlines()
            if "method mismatch prevents direct numeric comparison" in line
        )
        return (
            self.evidence_factory.create(
                source_id=source_id,
                artifact_type="table",
                parser_profile="synthetic_fixture_v1",
                artifact_locator=str(csv_path),
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
                artifact_locator=str(report_path),
                span_type="text",
                visible_text=conflict_text,
                page=3,
                stable_locator="section:discussion:block_002",
                validation_status="validated_rule",
                evidence_confidence=0.98,
                security_label="internal",
            ),
        )

    def _build_measurement(self, table_span: EvidenceSpan) -> PropertyMeasurement:
        measurement_id = fact_id(
            "measurement",
            {
                "experiment_id": "exp_nicu_aging_700c_8h",
                "property": "vickers_hardness",
                "value": 245,
                "unit": "HV",
            },
        )
        return PropertyMeasurement(
            measurement_id=measurement_id,
            experiment_id="exp_nicu_aging_700c_8h",
            property_id="prop_vickers_hardness",
            property_name="Твердость по Виккерсу",
            value=245,
            unit="HV",
            original_value="245 HV",
            method="Vickers HV10",
            supporting_span_ids=[table_span.span_id],
        )

    def _build_effect(
        self,
        measurement: PropertyMeasurement,
        table_span: EvidenceSpan,
    ) -> EffectClaim:
        return EffectClaim(
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
            supporting_span_ids=[table_span.span_id],
        )

    def _insert_evidence_span(
        self,
        connection: duckdb.DuckDBPyConnection,
        span: EvidenceSpan,
    ) -> None:
        connection.execute(
            """
            INSERT INTO evidence_spans (
              span_id,
              source_id,
              artifact_id,
              span_type,
              visible_text,
              page,
              locator_json,
              validation_status,
              evidence_confidence,
              security_label
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                span.span_id,
                span.source_id,
                span.artifact_id,
                span.span_type,
                span.visible_text,
                span.page,
                json.dumps(span.locator, ensure_ascii=False, sort_keys=True),
                span.validation_status,
                span.evidence_confidence,
                span.security_label,
            ],
        )

    def _insert_measurement(
        self,
        connection: duckdb.DuckDBPyConnection,
        measurement: PropertyMeasurement,
    ) -> None:
        connection.execute(
            """
            INSERT INTO property_measurements (
              measurement_id,
              experiment_id,
              property_id,
              property_name,
              value,
              unit,
              original_value,
              method,
              supporting_span_ids_json,
              validation_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                measurement.measurement_id,
                measurement.experiment_id,
                measurement.property_id,
                measurement.property_name,
                measurement.value,
                measurement.unit,
                measurement.original_value,
                measurement.method,
                json.dumps(measurement.supporting_span_ids, ensure_ascii=False),
                measurement.validation_status,
            ],
        )

    def _insert_effect(self, connection: duckdb.DuckDBPyConnection, effect: EffectClaim) -> None:
        connection.execute(
            """
            INSERT INTO effect_claims (
              effect_id,
              experiment_id,
              material_id,
              regime_id,
              property_id,
              direction,
              supporting_span_ids_json,
              baseline_measurement_id,
              treated_measurement_id,
              delta_value,
              delta_unit,
              qualitative_only,
              qualitative_summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                effect.effect_id,
                effect.experiment_id,
                effect.material_id,
                effect.regime_id,
                effect.property_id,
                effect.direction,
                json.dumps(effect.supporting_span_ids, ensure_ascii=False),
                effect.baseline_measurement_id,
                effect.treated_measurement_id,
                effect.delta_value,
                effect.delta_unit,
                effect.qualitative_only,
                effect.qualitative_summary,
            ],
        )

    def _evidence_from_row(self, row: tuple[Any, ...]) -> EvidenceSpan:
        return EvidenceSpan(
            span_id=str(row[0]),
            source_id=str(row[1]),
            artifact_id=str(row[2]),
            span_type=row[3],
            visible_text=str(row[4]),
            page=None if row[5] is None else int(row[5]),
            locator=json.loads(str(row[6])),
            validation_status=row[7],
            evidence_confidence=float(row[8]),
            security_label=row[9],
        )

    def _measurement_from_row(self, row: tuple[Any, ...]) -> PropertyMeasurement:
        return PropertyMeasurement(
            measurement_id=str(row[0]),
            experiment_id=str(row[1]),
            property_id=str(row[2]),
            property_name=str(row[3]),
            value=None if row[4] is None else float(row[4]),
            unit=None if row[5] is None else str(row[5]),
            original_value=None if row[6] is None else str(row[6]),
            method=None if row[7] is None else str(row[7]),
            supporting_span_ids=json.loads(str(row[8])),
            validation_status=row[9],
        )

    def _effect_from_row(self, row: tuple[Any, ...]) -> EffectClaim:
        return EffectClaim(
            effect_id=str(row[0]),
            experiment_id=str(row[1]),
            material_id=str(row[2]),
            regime_id=str(row[3]),
            property_id=str(row[4]),
            direction=row[5],
            supporting_span_ids=json.loads(str(row[6])),
            baseline_measurement_id=None if row[7] is None else str(row[7]),
            treated_measurement_id=None if row[8] is None else str(row[8]),
            delta_value=None if row[9] is None else float(row[9]),
            delta_unit=None if row[10] is None else str(row[10]),
            qualitative_only=bool(row[11]),
            qualitative_summary=str(row[12]),
        )
