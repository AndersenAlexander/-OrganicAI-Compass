import { apiClient } from "./client";
import type { PersistenceStatus } from "../types/persistence";

export async function getPersistenceStatus() {
  const { data } = await apiClient.get<PersistenceStatus>("/system/persistence");
  return data;
}
