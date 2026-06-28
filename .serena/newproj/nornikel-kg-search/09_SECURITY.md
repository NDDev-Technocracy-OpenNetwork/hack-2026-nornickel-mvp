# Security

## Threat Model

The system handles internal research documents, experiment data, staff/lab metadata, and generated analytical summaries. Main risks:

- unauthorized access to documents or source spans;
- object-level authorization bugs;
- leakage through LLM prompts or logs;
- prompt injection from untrusted documents;
- hallucinated or unsupported scientific claims;
- accidental exposure of personal or sensitive lab/team data;
- poisoned extraction due to malicious or malformed source files.

## Access Control

- Every source, chunk, claim, graph node, and relationship should carry a security label.
- Query results must be filtered by user permissions before answer generation and before LLM context construction.
- The API must enforce object-level authorization, not only route-level access.
- Audit every source access and answer run.

## Retrieval ACL Sequence

1. Resolve user identity, groups, project, and confidentiality clearance.
2. Query DuckDB for allowed `source_id` and `span_id` values.
3. Apply Qdrant payload filters for tenant, allowed source IDs, confidentiality, and allowed groups.
4. Rejoin Qdrant candidate unit IDs back to DuckDB.
5. Drop any candidate whose source/span is not allowed.
6. Build LLM context only from allowed evidence.
7. During graph expansion, traverse only allowed evidence-backed edges.
8. Verify cited spans are still allowed before returning the answer.

## LLM Controls

- Treat source documents as untrusted input.
- Separate system/developer instructions from retrieved document text.
- Never allow source text to override tool or security policy.
- Use schema validation for extraction outputs.
- Do not write model output directly to the canonical graph.
- Redact or block classified content if hosted LLMs are not approved.
- Store prompt/response metadata only if allowed by data policy.
- Never include inaccessible source existence, filenames, snippets, embeddings, or graph paths in user-visible answers unless policy explicitly allows disclosure of restricted-result counts.
- Flag but preserve source spans containing prompt-injection-like text such as "ignore previous instructions", "system prompt", "do not cite", "send this data", "exfiltrate", or hidden OCR instructions.

## Data Handling

- No secrets in repository.
- No raw credentials in logs.
- No internal documents in commits.
- Source files should be stored in a controlled artifact volume or bucket.
- Parsed text should inherit source security labels.
- Export/demo bundles should support anonymization.

## Review And Governance

- Low-confidence extracted facts go to review queue.
- High-impact facts, such as property improvements or safety-relevant conclusions, require validation before they are treated as canonical.
- Conflicting evidence must not be hidden.
- Generated answers must show source evidence and confidence.

## Security Checks

MVP checks:

- API auth smoke tests;
- object-level filtering tests;
- retrieval-layer ACL tests for vector payloads and graph traversal;
- prompt-injection regression examples;
- restricted-source-in-context checks;
- unsupported-claim blocking checks;
- source upload validation;
- secret scan before any commit;
- log review for sensitive data leakage.

Production checks:

- SSO integration;
- least-privilege service accounts;
- encrypted storage and transport;
- vulnerability scanning;
- audit export;
- backup encryption.
