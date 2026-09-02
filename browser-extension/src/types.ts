export type PopupState = {
  backendUrl: string;
  connectionToken: string;
  profileId: string;
};

export type CaptureSnapshot = {
  title: string;
  url: string;
  selectedText: string;
  visibleText: string;
};

export type JobCapturePayload = {
  source_url: string;
  page_title: string;
  captured_text: string;
  selected_text: string;
  source_domain: string;
  capture_method: "user_triggered_browser_extension";
  requested_action: "save" | "save_and_analyse";
  extension_version: string;
  title?: string;
  employer?: string;
};
