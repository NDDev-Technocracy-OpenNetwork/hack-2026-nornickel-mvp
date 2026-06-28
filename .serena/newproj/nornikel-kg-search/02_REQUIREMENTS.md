# Requirements

## Functional Requirements

### Ingestion

- Register every source document and structured file with stable source ID, checksum, version, confidentiality label, and import timestamp.
- Parse PDF, DOCX, XLSX/CSV, and JSON-like catalog exports.
- Split documents into chunks while preserving section titles, page numbers, table references, and source spans.
- Import dictionaries for materials, equipment, teams, labs, and topic tags before free-text extraction.
- Run idempotent ingestion: re-importing the same source must not duplicate canonical facts.

### Knowledge Extraction

- Extract entities: Material, Alloy, Element, MaterialComposition, Sample, BatchOrHeat, ProcessingRegime, ProcessStep, Experiment, Property, PropertyMeasurement, EffectClaim, Equipment, Installation, Team, Person, Lab, Document, Table, TableRow, TableCell, Figure, EvidenceSpan, Claim, Conclusion, Decision, ConflictGroup, DataGap.
- Extract relations with provenance and confidence.
- Normalize synonyms and aliases, especially alloy names, property names, equipment names, and regime labels.
- Separate raw extracted claims from validated canonical facts.
- Support human review for low-confidence or high-impact facts.

### Search And Analysis

- Support hybrid search over chunks, claims, and entity pages.
- Support structured filters: material, property, regime, equipment, lab, team, date, document type, confidence, validation status.
- Support graph traversal from any returned entity.
- Show graph paths used for answers.
- Detect and display conflicts: different effect directions, inconsistent property values, incompatible regimes, or contradictory conclusions.
- Identify data gaps: missing property measurements, no experiment under regime, no validated conclusion, or no recent replication.

### Question Answering

- Answer questions in Russian by default, with cited evidence.
- Return structured answer payloads: answer, evidence, graph paths, related entities, conflicts, gaps, and follow-up queries.
- Refuse or qualify answers when evidence is missing.
- Never invent measurements, teams, dates, or equipment.

### UI

- Single search and analysis workbench as the first screen.
- Evidence table with source snippets and provenance.
- Entity detail pages for materials, experiments, regimes, equipment, teams, and documents.
- Graph explorer focused on neighborhood expansion, not decorative graph visuals.
- Timeline view for experiment history and decisions.
- Gap board for missing or weakly supported facts.

## Nonfunctional Requirements

- MVP latency target: first answer under 8 seconds for medium queries after indexing.
- Search result latency target: under 2 seconds for top 20 hybrid results.
- Extraction jobs can be asynchronous.
- Every generated answer must be reproducible from stored retrieval inputs and source IDs.
- Data model must support future security filters at node, edge, and document level.
- Local demo must run from Docker Compose.
- MVP must have one hardened vertical slice before broad feature work: parse artifacts, search evidence, extract material-regime-property-measurement facts, write graph path, answer with citations, and show gaps.

## Acceptance Criteria

- Given a material/regime/property question, the system returns at least one grounded answer or a clear "not found" result with gaps.
- Each displayed fact links to source document, page/row, extraction method, confidence, and validation status.
- Graph view can expand from answer to material, experiments, regimes, equipment, teams, and source documents.
- Gap view lists missing measurements or untested combinations.
- Evaluation includes a small gold QA set and reports retrieval hit rate, citation coverage, and answer faithfulness.

## MVP Priority Boundaries

P0:

- artifact memory bank with Markdown, structured JSON, extracted tables/images, and manifest;
- source registry with checksum, security label, parser version, and artifact checksums;
- dictionary/rule/table-driven extraction for material, regime, property, measurement, and evidence spans;
- LLM JSON extraction only on small evidence chunks with schema validation;
- canonical graph path for Experiment to Sample to Material, ProcessingRegime/ProcessStep, PropertyMeasurement, Property, EvidenceSpan, and Document;
- hybrid retrieval over Markdown chunks, table rows, extracted claims, and entity summaries;
- answer table with cited evidence and explicit gaps.

P1:

- graph visualization around the answer path;
- contradiction detector;
- review queue;
- timeline and decision history;
- parser bakeoff across Docling, GROBID, Unstructured, Marker, and MinerU on hard documents.

P2:

- MatSciBERT and ChemDataExtractor integration;
- community/global GraphRAG summaries;
- active learning;
- complex ontology expansion;
- production SSO and external system integrations.

## Owner Decisions Needed

1. MVP priority:
   - A: question-answering demo first;
   - B: graph exploration first;
   - C: extraction/review quality first.
2. LLM policy:
   - A: hosted commercial model allowed;
   - B: only local/on-prem model allowed;
   - C: no LLM for classified data, only demo data.
3. Corpus form:
   - A: static dump of files;
   - B: live internal systems;
   - C: synthetic/anonymized sample.
4. Evaluation:
   - A: provide 20-50 gold questions;
   - B: infer evaluation from available corpus;
   - C: demo-only qualitative validation.
