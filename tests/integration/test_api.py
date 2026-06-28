from __future__ import annotations

from fastapi.testclient import TestClient

from services.api.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_qa_endpoint_returns_grounded_answer() -> None:
    client = TestClient(create_app())
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
