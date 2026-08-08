import { expect, test } from "@playwright/test";

test("complete adaptive roadmap flow with partial recalibration", async ({ page, request }, testInfo) => {
  const stamp = `e2e-${Date.now()}`;
  const api = "http://127.0.0.1:8000/api";
  const pageErrors:string[] = [];
  const consoleErrors:string[] = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  page.on("console", message => {
    if (message.type() !== "error") return;
    const text = message.text();
    if (!/WebGL|THREE\.WebGLRenderer|favicon/i.test(text)) consoleErrors.push(text);
  });

  const register = await request.post(`${api}/auth/register`, { data: { name:"Roadmap E2E", email:`${stamp}@example.test`, password:"E2e-roadmap-2026!" } });
  expect(register.ok()).toBeTruthy();
  const auth = await register.json();
  const headers = { Authorization:`Bearer ${auth.access_token}` };
  const diagnostic = await request.post(`${api}/diagnostics`, { headers, data: {
    interests:["responsible AI", "visual systems"], natural_activities:["designing workflows"], problems_noticed:["unclear AI adoption"], preferred_orientation:["systems", "people"], fears:["losing human judgment"], fear_intensity:4,
    ai_threat_or_opportunity:"An opportunity with human oversight", unclear_future:"How teams preserve agency", desired_world:"Responsible human-AI collaboration", values:["agency", "care", "learning"], contribution_if_supported:"Create practical responsible-AI guides", skills:["facilitation", "design"], preferred_learning_style:["project based"], cognitive_style:["visual", "systems"], ai_experience:"beginner", ai_tools_used:[], ai_confidence:4, ai_help_goals:["prototype", "learn"], preferred_interaction:"text", raw_answers:{ source:stamp }
  } });
  expect(diagnostic.ok()).toBeTruthy();
  const { profile_id:profileId } = await diagnostic.json();
  await page.addInitScript(token => localStorage.setItem("organicai.auth.token", token), auth.access_token);

  await page.goto(`/profile/${profileId}`);
  await expect(page.getByRole("heading", { name:"Your Human Potential Map" })).toBeVisible();
  await expect(page.getByText("This Human Potential Profile could not be loaded.")).toHaveCount(0);
  await page.getByRole("button", { name:"Workspace" }).click();
  await page.locator("#global-workspace-dropdown").getByRole("menuitem", { name:"Recommendations", exact:true }).click();
  await expect(page).toHaveURL(new RegExp(`/recommendations/${profileId}$`));
  await expect(page.getByRole("heading", { name:"Your Personalized Recommendations" })).toBeVisible();

  const recommendationList = await request.get(`${api}/recommendations/profile/${profileId}`, { headers });
  expect(recommendationList.ok()).toBeTruthy();
  let recommendations = await recommendationList.json();
  if (!recommendations.length) {
    const generated = await request.post(`${api}/recommendations/generate`, { headers, data:{ profile_id:profileId } });
    expect(generated.ok()).toBeTruthy();
    recommendations = (await generated.json()).recommendations;
    await page.reload();
  }
  const recommendation = recommendations.find((item:any) => item.status === "suggested");
  expect(recommendation).toBeTruthy();
  const recommendationId = recommendation.id as string;
  const card = page.locator(`[data-recommendation-id="${recommendationId}"]`);
  const acceptResponse = page.waitForResponse(response => response.url().endsWith(`/recommendations/${recommendationId}/accept`) && response.request().method() === "POST");
  await card.getByRole("button", { name:"Accept", exact:true }).click();
  expect((await acceptResponse).status()).toBe(200);
  await expect(card.getByText("accepted", { exact:true })).toBeVisible();

  const addResponsePromise = page.waitForResponse(response => response.url().endsWith(`/recommendations/${recommendationId}/add-to-roadmap`) && response.request().method() === "POST");
  await card.getByRole("button", { name:/Add to roadmap/i }).click();
  const addResponse = await addResponsePromise;
  expect(addResponse.status()).toBe(200);
  const added = await addResponse.json();
  const roadmapId = added.roadmap.id as string;
  await expect(card.getByRole("button", { name:/Add to roadmap/i })).toHaveCount(0);
  const actionsAfterAdd = await request.get(`${api}/roadmaps/${roadmapId}/actions`, { headers });
  expect(actionsAfterAdd.ok()).toBeTruthy();
  let actions = await actionsAfterAdd.json();
  expect(actions.filter((item:any) => item.recommendation_id === recommendationId)).toHaveLength(1);
  const actionId = actions.find((item:any) => item.recommendation_id === recommendationId).id as string;

  for (let index=0; index<4; index++) {
    const seeded = await request.post(`${api}/roadmaps/${roadmapId}/actions`, { headers, data:{ title:`${stamp} seeded action ${index+1}`, horizon:"seven_days", first_step:"Run a small deterministic step.", success_criteria:"Record the result.", priority:index+10, source_type:"user_created" } });
    expect(seeded.status()).toBe(200);
  }

  await page.getByRole("button", { name:"Workspace" }).click();
  await page.locator("#global-workspace-dropdown").getByRole("menuitem", { name:"My Roadmap", exact:true }).click();
  await expect(page).toHaveURL(new RegExp(`/roadmap/${profileId}$`));
  const actionCard = page.locator("article").filter({ has:page.getByRole("heading", { name:recommendation.title }) });
  await expect(actionCard.getByText("recommendation", { exact:true })).toBeVisible();
  const startResponse = page.waitForResponse(response => response.url().endsWith(`/roadmap-actions/${actionId}/start`) && response.request().method() === "POST");
  await actionCard.getByRole("button", { name:"Start", exact:true }).click();
  expect((await startResponse).status()).toBe(200);
  await expect(actionCard.getByText(/in progress/i)).toBeVisible();
  await page.reload();
  await expect(page.locator("article").filter({ hasText:recommendation.title }).getByText(/in progress/i)).toBeVisible();

  const reloadedCard = page.locator("article").filter({ has:page.getByRole("heading", { name:recommendation.title }) });
  await reloadedCard.getByRole("button", { name:"Expand" }).click();
  await reloadedCard.getByLabel("Completion note").fill("Completed during automated end-to-end validation.");
  const completeResponse = page.waitForResponse(response => response.url().endsWith(`/roadmap-actions/${actionId}/complete`) && response.request().method() === "POST");
  await reloadedCard.getByRole("button", { name:"Mark complete" }).click();
  expect((await completeResponse).status()).toBe(200);
  await page.reload();
  await expect(page.locator("article").filter({ hasText:recommendation.title }).getByText(/completed/i)).toBeVisible();
  const linkedRecommendation = await request.get(`${api}/recommendations/${recommendationId}`, { headers });
  expect((await linkedRecommendation.json()).status).toBe("completed");

  await page.getByRole("button", { name:"Check-ins" }).click();
  await page.getByLabel(/Energy/).fill("3"); await page.getByLabel(/Confidence/).fill("4"); await page.getByLabel(/Progress/).fill("4");
  await page.getByPlaceholder("What worked well?").fill("The structured first action was clear.");
  await page.getByPlaceholder("What blocked you?").fill("Limited available time.");
  await page.getByPlaceholder("What changed?").fill("I need a smaller workload next week.");
  const checkinResponsePromise = page.waitForResponse(response => response.url().endsWith(`/roadmaps/${roadmapId}/check-ins`) && response.request().method() === "POST");
  await page.getByRole("button", { name:"Save check-in" }).click();
  const checkinResponse = await checkinResponsePromise; expect(checkinResponse.status()).toBe(200);
  const checkInId = (await checkinResponse.json()).id as string;
  await expect(page.getByText("Check-in saved.")).toBeVisible();
  await page.reload(); await page.getByRole("button", { name:"Check-ins" }).click();
  await expect(page.getByText(/Limited available time/)).toBeVisible();

  const beforeProposal = await (await request.get(`${api}/roadmaps/${roadmapId}`, { headers })).json();
  const versionBefore = beforeProposal.version as number;
  const actionsBefore = await (await request.get(`${api}/roadmaps/${roadmapId}/actions`, { headers })).json();
  const proposalResponsePromise = page.waitForResponse(response => response.url().endsWith(`/roadmaps/${roadmapId}/recalibrate`) && response.request().method() === "POST");
  await page.getByRole("button", { name:"Recalibrate", exact:true }).click();
  const proposalResponse = await proposalResponsePromise; expect(proposalResponse.status()).toBe(200);
  const proposal = await proposalResponse.json(); expect(proposal.changes.length).toBeGreaterThanOrEqual(2);
  const unchanged = await (await request.get(`${api}/roadmaps/${roadmapId}/actions`, { headers })).json();
  expect(unchanged).toEqual(actionsBefore);
  const choices = page.getByTestId("recalibration-change").getByRole("checkbox");
  await expect(choices).toHaveCount(proposal.changes.length);
  for (let index=1; index<proposal.changes.length; index++) await choices.nth(index).uncheck();
  const applyResponsePromise = page.waitForResponse(response => response.url().endsWith(`/roadmaps/${roadmapId}/apply-recalibration`) && response.request().method() === "POST");
  await page.getByRole("button", { name:"Apply selected changes" }).click();
  const applyResponse = await applyResponsePromise; expect(applyResponse.status()).toBe(200);
  const appliedRoadmap = await applyResponse.json();
  const versionAfter = appliedRoadmap.version as number;
  expect(versionAfter).toBeGreaterThan(versionBefore);
  actions = await (await request.get(`${api}/roadmaps/${roadmapId}/actions`, { headers })).json();
  const selectedChange = proposal.changes[0];
  expect(actions.find((item:any) => item.id === selectedChange.action_id)?.status).toBe("postponed");
  for (const unselected of proposal.changes.slice(1)) expect(actions.find((item:any) => item.id === unselected.action_id)?.status).toBe("not_started");
  expect(actions.find((item:any) => item.id === actionId)?.status).toBe("completed");

  await page.getByRole("button", { name:"History" }).click();
  const versionsResponse = await request.get(`${api}/roadmaps/${roadmapId}/versions`, { headers }); expect(versionsResponse.status()).toBe(200);
  await expect(page.getByText(`Version ${versionAfter}`, { exact:false })).toBeVisible();
  await expect(page.getByText(`Version ${versionBefore}`, { exact:false })).toBeVisible();
  await page.locator('a[href="/my-journey"]').click();
  await expect(page.getByRole("heading", { name:/OrganicAI Compass/ })).toBeVisible();
  await expect(page.getByText(/completed/).first()).toBeVisible();
  await expect(page.getByText(/Limited available time/)).toBeVisible();
  await expect(page.getByText(new RegExp(`Roadmap version ${versionAfter}`))).toBeVisible();

  const reportResponsePromise = page.waitForResponse(response => response.url().endsWith(`/report/${profileId}`) && response.request().method() === "GET");
  await page.goto(`/report/${profileId}`);
  expect((await reportResponsePromise).status()).toBe(200);
  await expect(page.getByRole("heading", { name:"Human Potential Profile" })).toBeVisible();
  await expect(page.getByText(new RegExp(`Version ${versionAfter}`))).toBeVisible();
  await expect(page.getByText(/completed actions/)).toBeVisible();
  await expect(page.getByText(/active or remaining actions/)).toBeVisible();
  await expect(page.getByText(/Latest check-in summary/)).toBeVisible();
  await expect(page.getByText(/Recommendation-derived actions: 1/)).toBeVisible();

  const checkinsApi = await request.get(`${api}/roadmaps/${roadmapId}/check-ins`, { headers }); expect(checkinsApi.status()).toBe(200);
  expect((await checkinsApi.json()).some((item:any) => item.id === checkInId)).toBeTruthy();
  expect(pageErrors, `Uncaught page errors: ${pageErrors.join("\n")}`).toEqual([]);
  expect(consoleErrors, `Console errors: ${consoleErrors.join("\n")}`).toEqual([]);
  const ids = { profileId, recommendationId, roadmapId, actionId, checkInId, versionBefore, versionAfter, partialApplicationVerified:true };
  await testInfo.attach("adaptive-roadmap-ids", { body:JSON.stringify(ids, null, 2), contentType:"application/json" });
  console.log(`E2E_RESULT ${JSON.stringify(ids)}`);
});
