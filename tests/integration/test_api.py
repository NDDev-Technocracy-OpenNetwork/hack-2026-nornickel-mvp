from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from nornikel_kg.services import runtime
from services.api.main import create_app


def client_with_tmp_ledger(tmp_path: Path, monkeypatch: MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "catalog.duckdb"))
    runtime.get_ledger_repository.cache_clear()
    runtime.get_qa_service.cache_clear()
    return TestClient(create_app())


def test_health_endpoint(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    client = client_with_tmp_ledger(tmp_path, monkeypatch)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_qa_endpoint_returns_grounded_answer(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    client = client_with_tmp_ledger(tmp_path, monkeypatch)
    response = client.post(
        "/qa/ask",
        json={
            "question": "Что делали по Ni-30Cu при старении 700 C 8 ч?",
            "language": "ru",
            "include_graph": True,
            "include_gaps": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["verification"]["unsupported_claim_count"] == 0
    assert payload["experiments"]
    assert payload["evidence"]


def test_qa_endpoint_returns_gap_without_hallucinating(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    client = client_with_tmp_ledger(tmp_path, monkeypatch)
    response = client.post(
        "/qa/ask",
        json={
            "question": "Есть ли электропроводность для Ni-30Cu после старения 700 C 8 ч?",
            "language": "ru",
            "include_graph": True,
            "include_gaps": True,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer_summary"] == []
    assert payload["experiments"] == []
    assert payload["gaps"]
    assert payload["verification"]["unsupported_claim_count"] == 0


def test_sources_upload_and_evidence_listing(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    client = client_with_tmp_ledger(tmp_path, monkeypatch)
    csv_content = (
        "experiment_id,material,regime,temperature_c,duration_h,atmosphere,"
        "property,method,baseline_value,treated_value,unit,effect\n"
        "exp_api_upload,Ni-30Cu,aging,700,8,air,Vickers hardness,HV10,200,231,HV,increase\n"
    )

    upload = client.post(
        "/sources/upload",
        files={"file": ("uploaded.csv", csv_content, "text/csv")},
    )

    assert upload.status_code == 200
    source_id = upload.json()["source"]["source_id"]
    evidence = client.get(f"/sources/{source_id}/evidence")
    assert evidence.status_code == 200
    assert evidence.json()["evidence"][0]["span_type"] == "table_row"
