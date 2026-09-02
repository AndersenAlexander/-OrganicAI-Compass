import { expect, test } from "@playwright/test";

type PresentationQuestion = {
  question: string;
  source: "STATIC_KB" | "CAREER_HYPOTHESIS" | "EVIDENCE_PASSPORT" | "EXPERIMENT";
  expectedConcept: string;
};

const sequence: PresentationQuestion[] = [
  { question: "What is OrganicAI Compass?", source: "STATIC_KB", expectedConcept: "human-centred" },
  { question: "Why was this platform created?", source: "STATIC_KB", expectedConcept: "research prototype" },
  { question: "Does the LLM calculate my career scores?", source: "STATIC_KB", expectedConcept: "does not calculate" },
  { question: "What is my current career hypothesis?", source: "CAREER_HYPOTHESIS", expectedConcept: "persisted career hypotheses" },
  { question: "What evidence has been practically verified for my current direction?", source: "EVIDENCE_PASSPORT", expectedConcept: "practically verified" },
  { question: "Which evidence gaps remain unresolved?", source: "EVIDENCE_PASSPORT", expectedConcept: "evidence gaps" },
  { question: "What experiment should reduce that uncertainty?", source: "EXPERIMENT", expectedConcept: "persisted experiments" },
  { question: "What happens after an experiment is reviewed?", source: "STATIC_KB", expectedConcept: "evidence proposal" },
  { question: "How does Evidence Passport differ from self-reported skills?", source: "STATIC_KB", expectedConcept: "provenance" },
  { question: "Can you choose my career for me?", source: "STATIC_KB", expectedConcept: "decision remains yours" },
  { question: "What is the Human-AI Growth Roadmap?", source: "STATIC_KB", expectedConcept: "seven-day" },
  { question: "Why did you use RAG rather than fine-tuning?", source: "STATIC_KB", expectedConcept: "inspectable" },
  { question: "What happens if OpenAI is unavailable?", source: "STATIC_KB", expectedConcept: "degrade safely" },
  { question: "What role does ElevenLabs play?", source: "STATIC_KB", expectedConcept: "webrtc" },
  { question: "What are the main limitations of this prototype?", source: "STATIC_KB", expectedConcept: "no recorded participant-outcome" },
];

test("rehearses the complete presentation sequence against a disposable demo profile", async ({ page }, testInfo) => {
  test.setTimeout(180_000);
  const records: Array<Record<string, unknown>> = [];

  await page.goto("/login");
  await page.getByRole("button", { name: "Explore Demo", exact: true }).click();
  await expect(page).toHaveURL(/\/profile\/demo-profile$/);
  await page.goto("/coach/demo-profile");
  await expect(page.getByRole("heading", { name: "How can we move forward?" })).toBeVisible();

  const input = page.getByPlaceholder("Ask anything");
  for (const item of sequence) {
    const responsePromise = page.waitForResponse((response) => {
      if (!response.url().endsWith("/api/chat") || response.request().method() !== "POST") return false;
      return response.request().postDataJSON()?.message === item.question;
    });
    await input.fill(item.question);
    await page.getByRole("button", { name: "Send message" }).click();
    const response = await responsePromise;
    const payload = await response.json() as {
      answer: string;
      grounding_status: string;
      sources_used: unknown[];
      retrieval_status: { question_source?: string; retrieval_mode?: string };
    };

    const answer = payload.answer.toLowerCase();
    expect(response.status(), item.question).toBe(200);
    expect(payload.retrieval_status.question_source, item.question).toBe(item.source);
    expect(answer, item.question).toContain(item.expectedConcept);
    expect(payload.answer.split(/\s+/).filter(Boolean).length, item.question).toBeLessThanOrEqual(100);
    expect(payload.answer.toLowerCase(), item.question).not.toContain("api key");
    expect(payload.answer.toLowerCase(), item.question).not.toContain("conversation token");

    if (item.source === "STATIC_KB") {
      expect(payload.grounding_status, item.question).toBe("grounded");
      expect(payload.sources_used.length, item.question).toBeGreaterThan(0);
    } else {
      expect(payload.grounding_status, item.question).toBe("profile_grounded");
      expect(payload.retrieval_status.retrieval_mode, item.question).toBe("not_requested");
      expect(payload.sources_used, item.question).toEqual([]);
    }

    records.push({
      question: item.question,
      httpStatus: response.status(),
      source: payload.retrieval_status.question_source,
      retrievalMode: payload.retrieval_status.retrieval_mode,
      groundingStatus: payload.grounding_status,
      conciseForSpeech: payload.answer.split(/\s+/).filter(Boolean).length <= 100,
      answer: payload.answer,
    });
  }

  await page.reload();
  const refreshedInput = page.getByPlaceholder("Ask anything");
  const userContextQuestions = sequence.filter((item) => item.source !== "STATIC_KB");
  for (const item of userContextQuestions) {
    const refreshResponsePromise = page.waitForResponse((response) =>
      response.url().endsWith("/api/chat") && response.request().postDataJSON()?.message === item.question,
    );
    await refreshedInput.fill(item.question);
    await page.getByRole("button", { name: "Send message" }).click();
    const refreshResponse = await refreshResponsePromise;
    const refreshPayload = await refreshResponse.json() as {
      answer: string;
      grounding_status: string;
      sources_used: unknown[];
      retrieval_status: { question_source?: string; retrieval_mode?: string };
    };
    expect(refreshResponse.status(), item.question).toBe(200);
    expect(refreshPayload.grounding_status, item.question).toBe("profile_grounded");
    expect(refreshPayload.retrieval_status.question_source, item.question).toBe(item.source);
    expect(refreshPayload.retrieval_status.retrieval_mode, item.question).toBe("not_requested");
    expect(refreshPayload.sources_used, item.question).toEqual([]);
    expect(refreshPayload.answer.toLowerCase(), item.question).toContain(item.expectedConcept);

    records.push({
      question: `${item.question} (after refresh)`,
      httpStatus: refreshResponse.status(),
      source: refreshPayload.retrieval_status.question_source,
      retrievalMode: refreshPayload.retrieval_status.retrieval_mode,
      groundingStatus: refreshPayload.grounding_status,
      stateSurvivesRefresh: true,
      answer: refreshPayload.answer,
    });
  }
  await testInfo.attach("presentation-coach-rehearsal", { body: JSON.stringify(records, null, 2), contentType: "application/json" });
});
