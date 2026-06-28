# Conventions

- Evidence-led, table-led, schema-led design. Do not build generic chat/RAG behavior before the evidence ledger works.
- Separate IDs: `source_id`, `artifact_id`, `span_id`, `extraction_run_id`, `fact_id`, `claim_id`. Never include `extraction_run_id` in `span_id`.
- Table rows and table cells are first-class evidence units, not just Markdown text.
- Every final-answer sentence must cite `EvidenceSpan` IDs. Unsupported generated sentences are rejected or downgraded.
- ACL filtering happens before Qdrant context enters the LLM packet and is rechecked after retrieval.
- Keep external dependencies behind ports: ArtifactStore, MetadataStore, DocumentParser, VectorIndex, GraphStore, EmbeddingModel, SparseEncoder, LLM, ACLPolicy, EvaluationStore.
- Core domain services should remain concrete: EvidenceSpanFactory, TableEvidenceBuilder, MaterialNormalizer, RegimeNormalizer, MeasurementNormalizer, ConflictDetector, GapAnalyzer, AnswerAssembler, ClaimVerifier.