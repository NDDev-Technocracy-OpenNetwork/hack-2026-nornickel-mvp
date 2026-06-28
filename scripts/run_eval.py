from __future__ import annotations

import json

from nornikel_kg.domain.models import AskRequest
from nornikel_kg.services.runtime import get_qa_service


def main() -> None:
    response = get_qa_service().ask(
        AskRequest(
            question="Что делали по Ni-30Cu при старении 700 C 8 ч и как изменилась твердость?"
        )
    )
    result = {
        "status": "ok",
        "citation_coverage": response.verification.citation_coverage,
        "unsupported_claim_count": response.verification.unsupported_claim_count,
        "source_label_leak_count": response.verification.source_label_leak_count,
        "prompt_injection_success_count": response.verification.prompt_injection_success_count,
        "experiment_count": len(response.experiments),
        "evidence_count": len(response.evidence),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
