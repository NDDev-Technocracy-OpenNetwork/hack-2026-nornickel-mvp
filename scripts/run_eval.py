from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from nornikel_kg.domain.models import AskRequest
from nornikel_kg.services.runtime import get_ledger_repository, get_qa_service

EVAL_QUESTIONS = [
    {
        "question_id": "q_ideal_nicu_hardness",
        "question": "Что делали по Ni-30Cu при старении 700 C 8 ч и как изменилась твердость?",
        "min_experiment_count": 1,
        "min_evidence_count": 1,
        "expected_gap": False,
    },
    {
        "question_id": "q_gap_nicu_conductivity",
        "question": "Есть ли электропроводность для Ni-30Cu после старения 700 C 8 ч?",
        "min_experiment_count": 0,
        "min_evidence_count": 0,
        "expected_gap": True,
    },
    {
        "question_id": "q_conflict_method",
        "question": "Есть ли противоречия по твердости Ni-Cu после старения?",
        "min_experiment_count": 1,
        "min_evidence_count": 1,
        "expected_gap": False,
    },
]


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ["DUCKDB_PATH"] = str(Path(temp_dir) / "catalog.duckdb")
        get_ledger_repository.cache_clear()
        get_qa_service.cache_clear()
        service = get_qa_service()
        cases = []
        failed_cases = []
        for question in EVAL_QUESTIONS:
            response = service.ask(AskRequest(question=str(question["question"])))
            case = {
                "question_id": question["question_id"],
                "citation_coverage": response.verification.citation_coverage,
                "unsupported_claim_count": response.verification.unsupported_claim_count,
                "source_label_leak_count": response.verification.source_label_leak_count,
                "prompt_injection_success_count": (
                    response.verification.prompt_injection_success_count
                ),
                "experiment_count": len(response.experiments),
                "evidence_count": len(response.evidence),
                "gap_count": len(response.gaps),
            }
            cases.append(case)
            if response.verification.unsupported_claim_count != 0:
                failed_cases.append(f"{question['question_id']}: unsupported claims")
            if response.verification.source_label_leak_count != 0:
                failed_cases.append(f"{question['question_id']}: source-label leak")
            if len(response.experiments) < int(question["min_experiment_count"]):
                failed_cases.append(f"{question['question_id']}: missing experiments")
            if len(response.evidence) < int(question["min_evidence_count"]):
                failed_cases.append(f"{question['question_id']}: missing evidence")
            if bool(question["expected_gap"]) and not response.gaps:
                failed_cases.append(f"{question['question_id']}: missing expected gap")

        result = {
            "status": "ok" if not failed_cases else "failed",
            "case_count": len(cases),
            "failed_cases": failed_cases,
            "cases": cases,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if failed_cases:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
