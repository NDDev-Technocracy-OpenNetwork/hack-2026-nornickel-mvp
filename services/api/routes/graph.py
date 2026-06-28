from __future__ import annotations

from fastapi import APIRouter

from nornikel_kg.domain.models import AskRequest
from nornikel_kg.services.runtime import get_qa_service

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/demo-path")
def demo_path() -> dict[str, object]:
    response = get_qa_service().ask(
        AskRequest(question="Что делали по Ni-30Cu при старении 700 C 8 ч?")
    )
    path = response.graph_paths[0]
    node_types = [
        "Material",
        "Experiment",
        "Regime",
        "Step",
        "Measurement",
        "Property",
        "Evidence",
        "Document",
    ]
    return {
        "nodes": [
            {"id": node_id, "type": node_types[index], "label": node_id}
            for index, node_id in enumerate(path.nodes)
        ],
        "edges": [
            {
                "source": path.nodes[index],
                "target": path.nodes[index + 1],
                "label": relationship,
            }
            for index, relationship in enumerate(path.relationships)
        ],
    }
