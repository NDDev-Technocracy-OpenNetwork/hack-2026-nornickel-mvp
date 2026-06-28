from __future__ import annotations

from pathlib import Path

from nornikel_kg.adapters.duckdb.repositories import DuckDBLedgerRepository


def test_duckdb_ledger_seeds_synthetic_packet(tmp_path: Path) -> None:
    repository = DuckDBLedgerRepository(tmp_path / "catalog.duckdb")
    packet = repository.seed_synthetic_fixture(Path("sample_docs/synthetic"))

    assert packet.measurement.value == 245
    assert packet.measurement.unit == "HV"
    assert packet.effect.direction == "increase"
    assert packet.evidence[0].span_type == "table_row"

    loaded = repository.load_demo_packet()
    assert loaded.measurement.measurement_id == packet.measurement.measurement_id
    assert loaded.evidence[0].span_id == packet.evidence[0].span_id
