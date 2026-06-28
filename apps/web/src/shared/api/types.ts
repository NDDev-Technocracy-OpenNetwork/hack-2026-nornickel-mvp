export type EvidenceSpan = {
  span_id: string;
  source_id: string;
  artifact_id: string;
  span_type: "text" | "table_row" | "table_cell" | "figure" | "page_image";
  visible_text: string;
  page: number | null;
  validation_status: string;
  evidence_confidence: number;
  security_label: string;
};

export type AnswerSentence = {
  sentence: string;
  supporting_span_ids: string[];
  supporting_fact_ids: string[];
  graph_path_ids: string[];
};

export type ExperimentRow = {
  experiment_id: string;
  material_name: string;
  regime_summary: string;
  property_name: string;
  measurement: Record<string, unknown>;
  evidence_ids: string[];
  validation_status: string;
};

export type GraphPath = {
  path_id: string;
  nodes: string[];
  relationships: string[];
};

export type AskResponse = {
  run_id: string;
  answer_summary: AnswerSentence[];
  confidence: "low" | "medium" | "high";
  experiments: ExperimentRow[];
  evidence: EvidenceSpan[];
  graph_paths: GraphPath[];
  verification: {
    citation_coverage: number;
    unsupported_claim_count: number;
    source_label_leak_count: number;
    prompt_injection_success_count: number;
  };
  conflicts: Array<Record<string, unknown>>;
  gaps: Array<Record<string, unknown>>;
  follow_up_queries: string[];
};
