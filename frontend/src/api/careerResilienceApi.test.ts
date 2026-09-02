import { afterEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "./client";
import { confirmCareerExperimentRoadmap } from "./careerResilienceApi";

describe("career experiment roadmap confirmation", () => {
  afterEach(() => vi.restoreAllMocks());

  it("uses the explicit confirmation endpoint and returns the persisted session", async () => {
    const persisted = { id: "experiment-1", roadmap_action_id: "action-1" };
    const post = vi.spyOn(apiClient, "post").mockResolvedValue({ data: persisted } as never);

    await expect(confirmCareerExperimentRoadmap("experiment-1")).resolves.toEqual(persisted);
    expect(post).toHaveBeenCalledWith("/v1/career-experiment-sessions/experiment-1/roadmap", { confirmed: true });
  });
});
