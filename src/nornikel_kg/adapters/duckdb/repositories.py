from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from pathlib import Path
from typing import Any, cast

import duckdb
from nornikel_kg.domain.evidence import EvidenceSpanFactory
from nornikel_kg.domain.ids import claim_id, fact_id, source_id_from_bytes
from nornikel_kg.domain.ledger import EvidenceLedgerPacket
from nornikel_kg.domain.models import (
    EffectClaim,
    EffectDirection,
    EvidenceSpan,
    ExperimentRow,
    PropertyMeasurement,
    SourceIngestResponse,
    SourceSummary,
)


class SourceIngestError(ValueError):
    """Raised when uploaded source content is invalid."""

CSV_REQUIRED_COLUMNS = {
    "experiment_id",
    "material",
    "regime",
    "temperature_c",
    "duration_h",
    "atmosphere",
    "property",
    "method",
    "baseline_value",
    "treated_value",
    "unit",
    "effect",
}

EFFECT_DIRECTIONS = {"increase", "decrease", "no_change", "mixed", "unknown"}


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
            self._ensure_column(connection, "sources", "document_type", "TEXT DEFAULT 'report'")
            self._ensure_column(connection, "property_measurements", "source_id", "TEXT")
            self._ensure_column(connection, "effect_claims", "source_id", "TEXT")
            self._ensure_column(connection, "effect_claims", "material_name", "TEXT")
            self._ensure_column(connection, "effect_claims", "regime_summary", "TEXT")

    def seed_synthetic_fixture(self, sample_dir: Path) -> EvidenceLedgerPacket:
        self.migrate()
        csv_path = sample_dir / "mechanical_properties.csv"
        report_path = sample_dir / "nicu_aging_report.md"
        csv_bytes = csv_path.read_bytes()
        report_bytes = report_path.read_bytes()
        source_id = source_id_from_bytes(report_bytes + b"\n---\n" + csv_bytes)
        raw_sha256 = hashlib.sha256(report_bytes + csv_bytes).hexdigest()
        rows = self._parse_csv_rows(csv_bytes)

        with duckdb.connect(str(self.db_path)) as connection:
            try:
                connection.execute("BEGIN")
                self._delete_source_records(connection, source_id)
                self._register_source(
                    connection,
                    source_id=source_id,
                    title="Synthetic Ni-Cu aging report",
                    document_type="report+table",
                    raw_sha256=raw_sha256,
                    security_label="internal",
                )
                self._insert_csv_rows(
                    connection,
                    source_id=source_id,
                    rows=rows,
                    artifact_locator=str(csv_path),
                    parser_profile="synthetic_fixture_v1",
                    first_row_ordinal=3,
                )
                self._insert_markdown_evidence(
                    connection,
                    source_id=source_id,
                    text=report_path.read_text(encoding="utf-8"),
                    artifact_locator=str(report_path),
                    parser_profile="synthetic_fixture_v1",
                    selected_lines=(
                        "method mismatch prevents direct numeric comparison",
                        "not measured",
                    ),
                )
                connection.execute("COMMIT")
            except (SourceIngestError, ValueError):
                connection.execute("ROLLBACK")
                raise

        return self.load_demo_packet()

    def ingest_source_bytes(
        self,
        *,
        filename: str,
        content: bytes,
        title: str | None = None,
    ) -> SourceIngestResponse:
        self.migrate()
        source_id = source_id_from_bytes(content)
        raw_sha256 = hashlib.sha256(content).hexdigest()
        document_type = self._document_type_from_filename(filename)
        warnings: list[str] = []

        with duckdb.connect(str(self.db_path)) as connection:
            try:
                connection.execute("BEGIN")
                self._delete_source_records(connection, source_id)
                self._register_source(
                    connection,
                    source_id=source_id,
                    title=title or filename,
                    document_type=document_type,
                    raw_sha256=raw_sha256,
                    security_label="internal",
                )
                if document_type == "table":
                    rows = self._parse_csv_rows(content)
                    self._insert_csv_rows(
                        connection,
                        source_id=source_id,
                        rows=rows,
                        artifact_locator=filename,
                        parser_profile="csv_table_v1",
                        first_row_ordinal=1,
                    )
                else:
                    evidence_count = self._insert_markdown_evidence(
                        connection,
                        source_id=source_id,
                        text=content.decode("utf-8", errors="replace"),
                        artifact_locator=filename,
                        parser_profile="markdown_text_v1",
                        selected_lines=(),
                    )
                    if evidence_count == 0:
                        raise SourceIngestError("Markdown source has no extractable evidence.")
                connection.execute("COMMIT")
            except (SourceIngestError, ValueError):
                connection.execute("ROLLBACK")
                raise
            except Exception:
                connection.execute("ROLLBACK")
                raise

        source = next(item for item in self.list_sources() if item.source_id == source_id)
        return SourceIngestResponse(
            source=source,
            evidence_count=source.evidence_count,
            measurement_count=source.measurement_count,
            warnings=warnings,
        )

    def load_demo_packet(self) -> EvidenceLedgerPacket:
        self.migrate()
        with duckdb.connect(str(self.db_path)) as connection:
            source_rows = connection.execute(
                """
                SELECT source_id, title
                FROM sources
                ORDER BY created_at DESC, title
                """
            ).fetchall()
            source_titles = {str(row[0]): str(row[1]) for row in source_rows}
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
                ORDER BY source_id, page NULLS LAST, span_type DESC, span_id
                """
            ).fetchall()
            measurement_rows = connection.execute(
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
                ORDER BY experiment_id, measurement_id
                """
            ).fetchall()
            effect_rows = connection.execute(
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
                ORDER BY experiment_id, effect_id
                """
            ).fetchall()
            experiment_rows = connection.execute(
                """
                SELECT
                  m.measurement_id,
                  m.source_id,
                  m.experiment_id,
                  m.property_id,
                  m.property_name,
                  m.value,
                  m.unit,
                  m.validation_status,
                  e.material_id,
                  e.material_name,
                  e.regime_id,
                  e.regime_summary,
                  e.direction,
                  e.delta_value,
                  e.delta_unit,
                  e.supporting_span_ids_json
                FROM property_measurements m
                JOIN effect_claims e
                  ON m.experiment_id = e.experiment_id
                 AND m.property_id = e.property_id
                 AND m.source_id = e.source_id
                ORDER BY m.experiment_id, m.measurement_id
                """
            ).fetchall()

        evidence = [self._evidence_from_row(row) for row in evidence_rows]
        measurements = [self._measurement_from_row(row) for row in measurement_rows]
        effects = [self._effect_from_row(row) for row in effect_rows]
        experiments = [self._experiment_from_row(row) for row in experiment_rows]
        if not measurements or not effects:
            raise LookupError(
                "Evidence ledger has no measurements or effect claims. Seed fixtures first."
            )

        return EvidenceLedgerPacket(
            evidence=evidence,
            measurements=measurements,
            effects=effects,
            experiments=experiments,
            source_titles=source_titles,
            conflicts=self._build_conflicts(evidence),
            gaps=self._build_gaps(evidence, experiments),
        )

    def list_sources(self) -> list[SourceSummary]:
        self.migrate()
        with duckdb.connect(str(self.db_path)) as connection:
            rows = connection.execute(
                """
                SELECT
                  s.source_id,
                  s.title,
                  s.document_type,
                  s.security_label,
                  COUNT(DISTINCT ev.span_id) AS evidence_count,
                  COUNT(DISTINCT pm.measurement_id) AS measurement_count
                FROM sources s
                LEFT JOIN evidence_spans ev ON ev.source_id = s.source_id
                LEFT JOIN property_measurements pm ON pm.source_id = s.source_id
                GROUP BY s.source_id, s.title, s.document_type, s.security_label, s.created_at
                ORDER BY s.created_at DESC, s.title
                """
            ).fetchall()
        return [
            SourceSummary(
                source_id=str(row[0]),
                title=str(row[1]),
                document_type=str(row[2]),
                security_label=row[3],
                status="ledger",
                evidence_count=int(row[4]),
                measurement_count=int(row[5]),
            )
            for row in rows
        ]

    def get_source(self, source_id: str) -> SourceSummary | None:
        self.migrate()
        with duckdb.connect(str(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT
                  s.source_id,
                  s.title,
                  s.document_type,
                  s.security_label,
                  COUNT(DISTINCT ev.span_id) AS evidence_count,
                  COUNT(DISTINCT pm.measurement_id) AS measurement_count
                FROM sources s
                LEFT JOIN evidence_spans ev ON ev.source_id = s.source_id
                LEFT JOIN property_measurements pm ON pm.source_id = s.source_id
                WHERE s.source_id = ?
                GROUP BY s.source_id, s.title, s.document_type, s.security_label
                """,
                [source_id],
            ).fetchone()
        if row is None:
            return None
        return SourceSummary(
            source_id=str(row[0]),
            title=str(row[1]),
            document_type=str(row[2]),
            security_label=row[3],
            status="ledger",
            evidence_count=int(row[4]),
            measurement_count=int(row[5]),
        )

    def delete_source(self, source_id: str) -> bool:
        self.migrate()
        with duckdb.connect(str(self.db_path)) as connection:
            source = self._find_source(connection, source_id)
            if source is None:
                return False
            try:
                connection.execute("BEGIN")
                self._delete_source_records(connection, source_id)
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise
        return source is not None

    def list_evidence_spans(self, source_id: str | None = None) -> list[EvidenceSpan]:
        self.migrate()
        where_clause = "WHERE source_id = ?" if source_id else ""
        params: list[str] = [source_id] if source_id else []
        with duckdb.connect(str(self.db_path)) as connection:
            rows = connection.execute(
                f"""
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
                {where_clause}
                ORDER BY source_id, page NULLS LAST, span_type DESC, span_id
                """,
                params,
            ).fetchall()
        return [self._evidence_from_row(row) for row in rows]

    def _ensure_column(
        self,
        connection: duckdb.DuckDBPyConnection,
        table_name: str,
        column_name: str,
        column_type: str,
    ) -> None:
        existing = {
            str(row[1])
            for row in connection.execute(f"PRAGMA table_info('{table_name}')").fetchall()
        }
        if column_name not in existing:
            connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    def _delete_source_records(
        self,
        connection: duckdb.DuckDBPyConnection,
        source_id: str,
    ) -> None:
        connection.execute("DELETE FROM property_measurements WHERE source_id = ?", [source_id])
        connection.execute("DELETE FROM effect_claims WHERE source_id = ?", [source_id])
        connection.execute("DELETE FROM evidence_spans WHERE source_id = ?", [source_id])
        connection.execute("DELETE FROM sources WHERE source_id = ?", [source_id])

    def _find_source(
        self,
        connection: duckdb.DuckDBPyConnection,
        source_id: str,
    ) -> SourceSummary | None:
        row = connection.execute(
            """
            SELECT
              s.source_id,
              s.title,
              s.document_type,
              s.security_label
            FROM sources s
            WHERE s.source_id = ?
            """,
            [source_id],
        ).fetchone()
        if row is None:
            return None
        return SourceSummary(
            source_id=str(row[0]),
            title=str(row[1]),
            document_type=str(row[2]),
            security_label=row[3],
            status="ledger",
        )

    def _register_source(
        self,
        connection: duckdb.DuckDBPyConnection,
        *,
        source_id: str,
        title: str,
        document_type: str,
        raw_sha256: str,
        security_label: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO sources (source_id, title, document_type, raw_sha256, security_label)
            VALUES (?, ?, ?, ?, ?)
            """,
            [source_id, title, document_type, raw_sha256, security_label],
        )

    def _parse_csv_rows(self, content: bytes) -> list[dict[str, str]]:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise SourceIngestError("CSV source must be UTF-8 encoded.") from exc
        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames:
            raise SourceIngestError("CSV source has no header row.")

        normalized_fieldnames = [fieldname.strip() for fieldname in reader.fieldnames]
        missing_columns = sorted(CSV_REQUIRED_COLUMNS.difference(set(normalized_fieldnames)))
        if missing_columns:
            raise SourceIngestError(
                f"CSV source is missing required columns: {', '.join(missing_columns)}."
            )
        rows: list[dict[str, str]] = []
        for row in reader:
            normalized_row = {
                normalized_fieldnames[index]: (value.strip() if isinstance(value, str) else "")
                for index, value in enumerate(row.values())
            }
            rows.append(normalized_row)
        if not rows:
            raise SourceIngestError("CSV source has no data rows.")
        return rows

    def _insert_csv_rows(
        self,
        connection: duckdb.DuckDBPyConnection,
        *,
        source_id: str,
        rows: list[dict[str, str]],
        artifact_locator: str,
        parser_profile: str,
        first_row_ordinal: int,
    ) -> None:
        for index, row in enumerate(rows):
            row_ordinal = first_row_ordinal + index
            material_name = self._require_nonempty(row, "material", row_ordinal)
            material_id = self._material_id(material_name)
            regime_type = self._require_nonempty(row, "regime", row_ordinal).lower()
            temperature_c = self._parse_float(row, "temperature_c", row_ordinal)
            duration_h = self._parse_float(row, "duration_h", row_ordinal)
            atmosphere = self._require_nonempty(row, "atmosphere", row_ordinal)
            regime_id = self._regime_id(regime_type, temperature_c, duration_h, atmosphere)
            regime_summary = self._regime_summary(
                regime_type,
                temperature_c,
                duration_h,
                atmosphere,
            )
            property_raw = self._require_nonempty(row, "property", row_ordinal)
            method = self._require_nonempty(row, "method", row_ordinal)
            property_id = self._property_id(property_raw, method)
            property_name = self._property_name(property_raw, method)
            baseline_value = self._parse_float(row, "baseline_value", row_ordinal)
            treated_value = self._parse_float(row, "treated_value", row_ordinal)
            unit = self._require_nonempty(row, "unit", row_ordinal)
            direction = self._require_nonempty(row, "effect", row_ordinal).lower()
            if direction not in EFFECT_DIRECTIONS:
                raise SourceIngestError(
                    f"Row {row_ordinal}: unsupported effect value '{direction}'. "
                    f"Allowed: {', '.join(sorted(EFFECT_DIRECTIONS))}."
                )
            effect_direction = cast(EffectDirection, direction)
            delta_value = None
            if treated_value is not None and baseline_value is not None:
                delta_value = round(treated_value - baseline_value, 6)
            experiment_id = self._require_nonempty(row, "experiment_id", row_ordinal)
            table_text = self._table_row_text(
                material_name=material_name,
                regime=regime_type,
                temperature=temperature_c,
                duration=duration_h,
                atmosphere=atmosphere,
                property_name=property_name,
                method=method,
                baseline_value=baseline_value,
                treated_value=treated_value,
                unit=unit,
            )
            table_span = self.evidence_factory.create(
                source_id=source_id,
                artifact_type="table",
                parser_profile=parser_profile,
                artifact_locator=artifact_locator,
                span_type="table_row",
                visible_text=table_text,
                page=2,
                stable_locator=f"table_001:row_{row_ordinal:03d}",
                validation_status="validated_rule",
                evidence_confidence=1.0,
                security_label="internal",
            )
            measurement = PropertyMeasurement(
                measurement_id=fact_id(
                    "measurement",
                    {
                        "source_id": source_id,
                        "experiment_id": experiment_id,
                        "property": property_id,
                        "value": treated_value,
                        "unit": unit,
                    },
                ),
                experiment_id=experiment_id,
                property_id=property_id,
                property_name=property_name,
                value=treated_value,
                unit=unit,
                original_value=f"{treated_value:g} {unit}" if treated_value is not None else None,
                method=method,
                supporting_span_ids=[table_span.span_id],
            )
            effect = EffectClaim(
                effect_id=claim_id(
                    {
                        "source_id": source_id,
                        "experiment_id": experiment_id,
                        "direction": direction,
                        "supporting_span_ids": measurement.supporting_span_ids,
                    }
                ),
                experiment_id=experiment_id,
                material_id=material_id,
                regime_id=regime_id,
                property_id=property_id,
                direction=effect_direction,
                baseline_measurement_id=f"{measurement.measurement_id}_baseline",
                treated_measurement_id=measurement.measurement_id,
                delta_value=delta_value,
                delta_unit=unit,
                qualitative_summary=self._effect_summary(
                    material_name=material_name,
                    regime_summary=regime_summary,
                    property_name=property_name,
                    direction=direction,
                    treated_value=treated_value,
                    delta_value=delta_value,
                    unit=unit,
                ),
                supporting_span_ids=[table_span.span_id],
            )

            self._delete_fact_records(connection, measurement.measurement_id, effect.effect_id)
            self._insert_evidence_span(connection, table_span)
            self._insert_measurement(connection, measurement, source_id=source_id)
            self._insert_effect(
                connection,
                effect,
                source_id=source_id,
                material_name=material_name,
                regime_summary=regime_summary,
            )

    def _insert_markdown_evidence(
        self,
        connection: duckdb.DuckDBPyConnection,
        *,
        source_id: str,
        text: str,
        artifact_locator: str,
        parser_profile: str,
        selected_lines: tuple[str, ...],
    ) -> int:
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if selected_lines:
            lines = [
                line
                for line in lines
                if any(selected_line in line for selected_line in selected_lines)
            ]

        for index, line in enumerate(lines, start=2):
            stable_locator = (
                "section:discussion:block_002"
                if "method mismatch prevents direct numeric comparison" in line
                else f"section:text:block_{index:03d}"
            )
            span = self.evidence_factory.create(
                source_id=source_id,
                artifact_type="text",
                parser_profile=parser_profile,
                artifact_locator=artifact_locator,
                span_type="text",
                visible_text=line,
                page=3,
                stable_locator=stable_locator,
                validation_status="validated_rule",
                evidence_confidence=0.98,
                security_label="internal",
            )
            self._insert_evidence_span(connection, span)

        return len(lines)

    def _delete_fact_records(
        self,
        connection: duckdb.DuckDBPyConnection,
        measurement_id: str,
        effect_id: str,
    ) -> None:
        connection.execute(
            "DELETE FROM property_measurements WHERE measurement_id = ?",
            [measurement_id],
        )
        connection.execute("DELETE FROM effect_claims WHERE effect_id = ?", [effect_id])

    def _insert_evidence_span(
        self,
        connection: duckdb.DuckDBPyConnection,
        span: EvidenceSpan,
    ) -> None:
        connection.execute("DELETE FROM evidence_spans WHERE span_id = ?", [span.span_id])
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
        *,
        source_id: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO property_measurements (
              measurement_id,
              source_id,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                measurement.measurement_id,
                source_id,
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

    def _insert_effect(
        self,
        connection: duckdb.DuckDBPyConnection,
        effect: EffectClaim,
        *,
        source_id: str,
        material_name: str,
        regime_summary: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO effect_claims (
              effect_id,
              source_id,
              experiment_id,
              material_id,
              material_name,
              regime_id,
              regime_summary,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                effect.effect_id,
                source_id,
                effect.experiment_id,
                effect.material_id,
                material_name,
                effect.regime_id,
                regime_summary,
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

    def _experiment_from_row(self, row: tuple[Any, ...]) -> ExperimentRow:
        evidence_ids = json.loads(str(row[15]))
        return ExperimentRow(
            source_id=str(row[1]),
            experiment_id=str(row[2]),
            material_id=str(row[8]),
            material_name=str(row[9]),
            regime_id=str(row[10]),
            regime_summary=str(row[11]),
            property_id=str(row[3]),
            property_name=str(row[4]),
            measurement={
                "value": None if row[5] is None else float(row[5]),
                "unit": None if row[6] is None else str(row[6]),
                "delta_value": None if row[13] is None else float(row[13]),
                "delta_unit": None if row[14] is None else str(row[14]),
                "effect_direction": str(row[12]),
            },
            evidence_ids=evidence_ids,
            validation_status=row[7],
        )

    def _build_conflicts(self, evidence: list[EvidenceSpan]) -> list[dict[str, object]]:
        conflicts: list[dict[str, object]] = []
        method_spans = [
            span
            for span in evidence
            if "method mismatch prevents direct numeric comparison" in span.visible_text
        ]
        if method_spans:
            conflicts.append(
                {
                    "conflict_group_id": "conf_nicu_hardness_method",
                    "type": "method_mismatch",
                    "summary": (
                        "Похожий режим в соседнем источнике измерен другим методом, "
                        "поэтому не сравнивается напрямую с HV."
                    ),
                    "supporting_span_ids": [span.span_id for span in method_spans],
                }
            )
        return conflicts

    def _build_gaps(
        self,
        evidence: list[EvidenceSpan],
        experiments: list[ExperimentRow],
    ) -> list[dict[str, object]]:
        has_conductivity = any(
            "conductivity" in experiment.property_name.lower()
            or "электропровод" in experiment.property_name.lower()
            for experiment in experiments
        )
        near_miss_ids = [
            span.span_id
            for span in evidence
            if "not measured" in span.visible_text.lower()
            or "электропровод" in span.visible_text.lower()
            or span.span_type == "table_row"
        ]
        if has_conductivity or not near_miss_ids:
            return []
        return [
            {
                "gap_id": "gap_nicu_conductivity_aging_700c",
                "type": "missing_measurement",
                "description": (
                    "Для Ni-Cu после старения 700 C / 8 ч нет валидированного "
                    "измерения электропроводности в доступном ledger."
                ),
                "near_miss_evidence_span_ids": near_miss_ids[:3],
            }
        ]

    def _document_type_from_filename(self, filename: str) -> str:
        return "table" if filename.lower().endswith(".csv") else "document"

    def _material_id(self, material_name: str) -> str:
        normalized = material_name.lower().replace(" ", "")
        known = {
            "ni-30cu": "mat_nicu_30",
            "nicu30": "mat_nicu_30",
            "cuni30": "mat_cuni_30",
            "cu-ni30": "mat_cuni_30",
        }
        return known.get(normalized, f"mat_{self._slug(material_name)}")

    def _property_id(self, property_raw: str, method: str) -> str:
        lowered = f"{property_raw} {method}".lower()
        if "vickers" in lowered:
            return "prop_vickers_hardness"
        if "rockwell" in lowered:
            return "prop_rockwell_hardness"
        if "conductivity" in lowered or "электропровод" in lowered:
            return "prop_conductivity"
        return f"prop_{self._slug(property_raw)}"

    def _property_name(self, property_raw: str, method: str) -> str:
        lowered = f"{property_raw} {method}".lower()
        if "vickers" in lowered:
            return "Твердость по Виккерсу"
        if "rockwell" in lowered:
            return "Твердость по Роквеллу"
        if "conductivity" in lowered or "электропровод" in lowered:
            return "Электропроводность"
        return property_raw

    def _regime_id(
        self,
        regime_type: str,
        temperature_c: float | None,
        duration_h: float | None,
        atmosphere: str,
    ) -> str:
        temp = "unknown" if temperature_c is None else f"{temperature_c:g}c"
        duration = "unknown" if duration_h is None else f"{duration_h:g}h"
        return f"reg_{self._slug(regime_type)}_{temp}_{duration}_{self._slug(atmosphere)}"

    def _regime_summary(
        self,
        regime_type: str,
        temperature_c: float | None,
        duration_h: float | None,
        atmosphere: str,
    ) -> str:
        regime_ru = {"aging": "Старение", "annealing": "Отжиг"}.get(regime_type, regime_type)
        temp = "?" if temperature_c is None else f"{temperature_c:g} C"
        duration = "?" if duration_h is None else f"{duration_h:g} ч"
        return f"{regime_ru}, {temp}, {duration}, {atmosphere}"

    def _effect_summary(
        self,
        *,
        material_name: str,
        regime_summary: str,
        property_name: str,
        direction: str,
        treated_value: float | None,
        delta_value: float | None,
        unit: str,
    ) -> str:
        direction_ru = {
            "increase": "повысил",
            "decrease": "снизил",
            "no_change": "не изменил",
            "mixed": "дал смешанный эффект на",
            "unknown": "имеет неизвестный эффект на",
        }[direction]
        value = (
            "без численного значения"
            if treated_value is None
            else f"до {treated_value:g} {unit}"
        )
        delta = "" if delta_value is None else f" (Δ {delta_value:g} {unit})"
        return (
            f"{regime_summary} для {material_name} {direction_ru} "
            f"{property_name} {value}{delta}."
        )

    def _table_row_text(
        self,
        *,
        material_name: str,
        regime: str,
        temperature: float | None,
        duration: float | None,
        atmosphere: str,
        property_name: str,
        method: str,
        baseline_value: float | None,
        treated_value: float | None,
        unit: str,
    ) -> str:
        baseline = "unknown" if baseline_value is None else f"{baseline_value:g} {unit}"
        treated = "unknown" if treated_value is None else f"{treated_value:g} {unit}"
        temperature_text = "?" if temperature is None else f"{temperature:g}"
        duration_text = "?" if duration is None else f"{duration:g}"
        return (
            f"Sample {material_name}-A | {regime.title()} {temperature_text} C | "
            f"{duration_text} h | {atmosphere} | {property_name} {method} | "
            f"baseline {baseline} | treated {treated}"
        )

    def _parse_float(self, row: dict[str, str], field: str, row_number: int) -> float:
        raw = row.get(field)
        if raw is None:
            raise SourceIngestError(f"Row {row_number}: missing required numeric field '{field}'.")
        stripped = raw.strip()
        if not stripped:
            raise SourceIngestError(f"Row {row_number}: field '{field}' is required.")
        try:
            return float(stripped)
        except ValueError as exc:
            raise SourceIngestError(
                f"Row {row_number}: field '{field}' must be a numeric value."
            ) from exc

    def _require_nonempty(self, row: dict[str, str], field: str, row_number: int) -> str:
        raw = row.get(field)
        if raw is None:
            raise SourceIngestError(f"Row {row_number}: missing required field '{field}'.")
        value = raw.strip()
        if not value:
            raise SourceIngestError(f"Row {row_number}: field '{field}' is required.")
        return value

    def _slug(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
