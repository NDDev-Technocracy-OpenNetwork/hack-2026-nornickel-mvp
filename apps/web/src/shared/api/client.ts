import type { AskResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_BASE_URL}/qa/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      language: "ru",
      include_graph: true,
      include_gaps: true,
    }),
  });

  if (!response.ok) {
    throw new Error(`QA request failed with ${response.status}`);
  }

  return (await response.json()) as AskResponse;
}
