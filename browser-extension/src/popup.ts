import type { CaptureSnapshot, JobCapturePayload, PopupState } from "./types";

const EXTENSION_VERSION = "0.1.0";

function getInput(id: string) {
  const element = document.getElementById(id);
  if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement)) {
    throw new Error(`Missing popup field: ${id}`);
  }
  return element;
}

function setStatus(message: string) {
  const element = document.getElementById("status");
  if (element) element.textContent = message;
}

async function loadState(): Promise<PopupState> {
  const stored = await chrome.storage.local.get(["backendUrl", "connectionToken", "profileId"]);
  return {
    backendUrl: String(stored.backendUrl || "http://127.0.0.1:8000/api"),
    connectionToken: String(stored.connectionToken || ""),
    profileId: String(stored.profileId || ""),
  };
}

async function saveState() {
  await chrome.storage.local.set({
    backendUrl: getInput("backendUrl").value.trim(),
    connectionToken: getInput("connectionToken").value.trim(),
    profileId: getInput("profileId").value.trim(),
  });
}

function pageSnapshot(): CaptureSnapshot {
  const selection = window.getSelection()?.toString() || "";
  const visibleText = document.body?.innerText || "";
  return {
    title: document.title || "",
    url: location.href,
    selectedText: selection.slice(0, 24000),
    visibleText: visibleText.slice(0, 24000),
  };
}

async function captureActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab.id || !tab.url) throw new Error("No active tab is available.");
  const [result] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: pageSnapshot,
  });
  const snapshot = result.result as CaptureSnapshot;
  getInput("sourceUrl").value = snapshot.url;
  getInput("sourceDomain").value = new URL(snapshot.url).hostname;
  getInput("jobTitle").value = snapshot.title.split(" - ")[0] || snapshot.title;
  getInput("employer").value = snapshot.title.includes(" - ") ? snapshot.title.split(" - ").slice(1).join(" - ") : "";
  getInput("capturedText").value = snapshot.selectedText || snapshot.visibleText;
  const lowQuality = (snapshot.selectedText || snapshot.visibleText).trim().length < 180;
  const notice = document.getElementById("qualityNotice");
  if (notice) notice.hidden = !lowQuality;
}

function payloadFor(action: "save" | "save_and_analyse"): JobCapturePayload {
  const sourceUrl = getInput("sourceUrl").value.trim();
  return {
    source_url: sourceUrl,
    page_title: getInput("jobTitle").value.trim(),
    captured_text: getInput("capturedText").value,
    selected_text: "",
    source_domain: sourceUrl ? new URL(sourceUrl).hostname : "",
    capture_method: "user_triggered_browser_extension",
    requested_action: action,
    extension_version: EXTENSION_VERSION,
    title: getInput("jobTitle").value.trim(),
    employer: getInput("employer").value.trim(),
  };
}

async function submit(action: "save" | "save_and_analyse") {
  await saveState();
  const backendUrl = getInput("backendUrl").value.trim().replace(/\/$/, "");
  const rawProfileId = getInput("profileId").value.trim();
  const token = getInput("connectionToken").value.trim();
  if (!rawProfileId) throw new Error("Profile ID is required. Copy it from the Browser Extension settings page in OrganicAI Compass.");
  if (!token) throw new Error("Connection token is required.");
  const profileId = encodeURIComponent(rawProfileId);
  const response = await fetch(`${backendUrl}/v1/profiles/${profileId}/job-captures`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-OrganicAI-Extension-Token": token,
    },
    body: JSON.stringify(payloadFor(action)),
  });
  if (!response.ok) {
    throw new Error(messageForStatus(response.status));
  }
  const result = await response.json();
  setStatus(result.status === "Duplicate" ? "Duplicate capture found in OrganicAI Compass." : "Capture saved.");
}

function messageForStatus(status: number) {
  if (status === 401) return "Login or a valid extension connection is required.";
  if (status === 403) return "Capture was rejected. Check that the token belongs to this profile and has not expired.";
  if (status === 404) return "Profile or extension connection was not found.";
  if (status === 422) return "Capture could not be saved. Review the URL, selected text, and connection details.";
  return "Capture failed. Try again from OrganicAI Compass after refreshing the connection token.";
}

async function initialise() {
  const state = await loadState();
  getInput("backendUrl").value = state.backendUrl;
  getInput("connectionToken").value = state.connectionToken;
  getInput("profileId").value = state.profileId;
  await captureActiveTab();
  getInput("editButton").addEventListener("click", () => getInput("capturedText").focus());
  getInput("cancelButton").addEventListener("click", () => window.close());
  getInput("saveButton").addEventListener("click", () => submit("save").catch((error: Error) => setStatus(error.message)));
  getInput("saveAnalyseButton").addEventListener("click", () => submit("save_and_analyse").catch((error: Error) => setStatus(error.message)));
}

initialise().catch((error: Error) => setStatus(error.message));
