import type {
  AskFilters,
  AskResponse,
  SourceIngestResponse,
  SourceSummary,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

function hasNonEmptyFilters(filters: AskFilters | undefined): filters is AskFilters {
  if (!filters) {
    return false;
  }

  return Object.values(filters).some((values) => values.length > 0);
}

export async function askQuestion(question: string, filters?: AskFilters): Promise<AskResponse> {
  const body: {
    question: string;
    language: "ru" | "en";
    include_graph: boolean;
    include_gaps: boolean;
    filters?: AskFilters;
  } = {
    question,
    language: "ru",
    include_graph: true,
    include_gaps: true,
  };

  if (hasNonEmptyFilters(filters)) {
    body.filters = filters;
  }

  const response = await fetch(`${API_BASE_URL}/qa/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`QA request failed with ${response.status}`);
  }

  return (await response.json()) as AskResponse;
}

export async function listSources(): Promise<SourceSummary[]> {
  const response = await fetch(`${API_BASE_URL}/sources`);

  if (!response.ok) {
    throw new Error(`Sources request failed with ${response.status}`);
  }

  const payload = (await response.json()) as { sources: SourceSummary[] };
  return payload.sources;
}

export async function uploadSource(file: File): Promise<SourceIngestResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/sources/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Source upload failed with ${response.status}`);
  }

  return (await response.json()) as SourceIngestResponse;
}

export async function deleteSource(sourceId: string): Promise<{ source_id: string; deleted: boolean }> {
  const response = await fetch(`${API_BASE_URL}/sources/${sourceId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Source delete failed with ${response.status}`);
  }

  return (await response.json()) as { source_id: string; deleted: boolean };
}
