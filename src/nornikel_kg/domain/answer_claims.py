from __future__ import annotations

from nornikel_kg.domain.models import AnswerSentence, AnswerVerification, EvidenceSpan
from nornikel_kg.domain.security import SourceLabelPolicy


class ClaimVerifier:
    def verify(
        self,
        *,
        answer_summary: list[AnswerSentence],
        evidence_spans: list[EvidenceSpan],
        source_label_policy: SourceLabelPolicy,
    ) -> AnswerVerification:
        supported = [sentence for sentence in answer_summary if sentence.supporting_span_ids]
        unsupported_claim_count = len(answer_summary) - len(supported)
        citation_coverage = 1.0 if not answer_summary else len(supported) / len(answer_summary)

        span_by_id = {span.span_id: span for span in evidence_spans}
        source_label_leak_count = 0
        for sentence in answer_summary:
            for span_id in sentence.supporting_span_ids:
                span = span_by_id.get(span_id)
                if span is None or not source_label_policy.is_allowed(span):
                    source_label_leak_count += 1

        return AnswerVerification(
            citation_coverage=citation_coverage,
            unsupported_claim_count=unsupported_claim_count,
            source_label_leak_count=source_label_leak_count,
        )
