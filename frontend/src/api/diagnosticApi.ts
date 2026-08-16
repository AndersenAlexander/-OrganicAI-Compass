import { apiClient } from "./client";
import type { DiagnosticPayload, DiagnosticResponse } from "../types/diagnostic";

export async function submitDiagnostic(payload: DiagnosticPayload) {
  const { data } = await apiClient.post<DiagnosticResponse>("/diagnostics", payload);
  return data;
}
