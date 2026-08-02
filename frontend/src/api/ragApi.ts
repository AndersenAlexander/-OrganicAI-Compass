import { apiClient } from "./client";

export type RagResult = { id: string; document_name: string; section_title: string; chunk_text: string; score: number };

export async function searchKnowledgeBase(query: string) {
  const { data } = await apiClient.get<{ query: string; results: RagResult[] }>("/rag/search", { params: { query } });
  return data;
}

export async function askKnowledgeBase(query: string) {
  const { data } = await apiClient.post<{ query: string; sources: RagResult[]; has_sources: boolean }>("/rag/ask", { query });
  return data;
}

export async function reindexKnowledgeBase() {
  const { data } = await apiClient.post<{ documents: number; chunks: number }>("/rag/reindex");
  return data;
}
