import type {
  AskFilters,
  AskResponse,
  SourceIngestResponse,
  SourceSummary,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

type ErrorPayload = {
  detail?: unknown;
};

function formatServerErrorDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (typeof item === "object" && item !== null) {
          if (
            "loc" in item &&
            typeof item.msg === "string" &&
            Array.isArray(item.loc)
          ) {
            const location = item.loc.join(".");
            return `${location}: ${item.msg}`;
          }
          if ("msg" in item && typeof item.msg === "string") {
            return item.msg as string;
          }
        }
        return JSON.stringify(item);
      })
      .filter((item) => item.length > 0)
      .join(" | ");
  }
  if (typeof detail === "object" && detail !== null) {
    return JSON.stringify(detail);
  }
  return "Unknown error";
}

async function readErrorMessage(response: Response, context: string): Promise<string> {
  try {
    const payload = (await response.json()) as ErrorPayload;
    if (payload && "detail" in payload) {
      const message = formatServerErrorDetail(payload.detail);
      return `${context}: ${message}`;
    }
  } catch {
    // keep fallback below
  }
  return `${context}: ${response.status}`;
}

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
    throw new Error(await readErrorMessage(response, "QA request failed"));
  }

  return (await response.json()) as AskResponse;
}

export async function listSources(): Promise<SourceSummary[]> {
  const response = await fetch(`${API_BASE_URL}/sources`);

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Sources request failed"));
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
    throw new Error(await readErrorMessage(response, "Source upload failed"));
  }

  return (await response.json()) as SourceIngestResponse;
}

export async function deleteSource(sourceId: string): Promise<{ source_id: string; deleted: boolean }> {
  const response = await fetch(`${API_BASE_URL}/sources/${sourceId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Source delete failed"));
  }

  return (await response.json()) as { source_id: string; deleted: boolean };
}
