# Data Model

## Canonical Entity Model

### Material And Composition

- Material: stable material or alloy family.
- Alloy: named alloy or composition variant.
- Element: chemical element.
- Composition: element percentages, uncertainty, source.

### Experiment And Sample

- Experiment: planned or executed research activity.
- Sample: physical specimen or batch.
- ProcessingRegime: temperature, pressure, atmosphere, time, cooling, deformation, heat treatment, or other process parameters.
- Equipment: machine or measurement device.
- Installation: physical setup or facility.

### Properties And Results

- Property: tensile strength, hardness, corrosion resistance, phase composition, conductivity, etc.
- PropertyMeasurement: value, unit, method, uncertainty, conditions, direction of change.
- Effect: increase, decrease, no change, threshold behavior, tradeoff, or qualitative effect.

### Knowledge Objects

- Document: source article, report, protocol, table, presentation, or catalog row.
- EvidenceSpan: stable text, table cell/row, figure, image, or page region that can support a fact.
- Claim: extracted statement backed by source span.
- Conclusion: author or reviewer conclusion.
- Decision: project/lab decision derived from evidence.
- Gap: missing, weak, conflicting, outdated, or unreplicated data.

### Organization

- Person.
- Team.
- Lab.
- Project.
- TopicTag.

## Provenance Shape

Every fact-like node or relationship stores:

- `source_id`;
- `span_id`;
- `artifact_id`;
- `artifact_type`;
- `parser_name`;
- `parser_version`;
- `source_version`;
- `extraction_run_id`;
- `extraction_method`;
- `confidence`;
- `validation_status`;
- `reviewer_id`;
- `created_at`;
- `updated_at`.

This follows the PROV-O idea that information is produced by activities, derived from entities, and associated with agents.

## Entity Resolution

Resolution layers:

1. Exact dictionary match.
2. Alias/synonym match.
3. Unit and composition normalization.
4. Embedding-assisted candidate match.
5. Human review for ambiguous or high-impact merges.

Do not merge entities automatically when composition, regime parameters, or equipment identity conflict.

## Gap Model

Gap types:

- missing_property_measurement;
- missing_exact_regime;
- missing_equipment_metadata;
- unvalidated_claim;
- conflicting_effect;
- outdated_result;
- no_replication;
- source_access_restricted.

Gap records should reference the expected entity pair or path and the evidence that made the gap visible.

## P0 Graph Path Contract

The first working product must support this canonical path:

```text
Material
  <-[:USES_MATERIAL]- Experiment
  -[:APPLIES_REGIME]-> ProcessingRegime
  -[:HAS_MEASUREMENT]-> PropertyMeasurement
  -[:OF_PROPERTY]-> Property
PropertyMeasurement
  -[:SUPPORTED_BY]-> EvidenceSpan
EvidenceSpan
  -[:FROM_DOCUMENT]-> Document
Experiment
  -[:PERFORMED_BY]-> Team
Experiment
  -[:USED_EQUIPMENT]-> Equipment
```

All other graph relationships are secondary until this path works end to end.

## Indexing Strategy

Graph indexes:

- canonical IDs;
- aliases;
- material labels;
- property names;
- regime parameter buckets;
- source IDs;
- validation status.

Vector payload filters:

- material IDs;
- property IDs;
- regime IDs;
- equipment IDs;
- lab/team IDs;
- document type;
- date;
- security label;
- validation status.

## Data Quality Rules

- Measurements require units.
- Regimes require typed parameters where available.
- Claims require source spans.
- Final-answer claims require `EvidenceSpan`; generic Markdown chunks are not enough.
- Conclusions require either source support or reviewer authoring.
- Decisions require actor, date, rationale, and linked evidence or gap.
