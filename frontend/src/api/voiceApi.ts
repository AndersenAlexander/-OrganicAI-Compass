import { apiClient } from "./client";

function resolveAudioUrl(audioUrl: string) {
  const baseUrl = apiClient.defaults.baseURL;
  if (!audioUrl || !audioUrl.startsWith("/") || !baseUrl?.startsWith("http")) return audioUrl;

  const apiOrigin = new URL(baseUrl).origin;
  return `${apiOrigin}${audioUrl}`;
}

export async function transcribeAudio(audioBlob: Blob): Promise<{ transcript: string }> {
  const formData = new FormData();
  formData.append("file", audioBlob, "voice-message.webm");
  const { data } = await apiClient.post<{ transcript: string }>("/voice/transcribe", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}

export async function synthesizeSpeech(text: string): Promise<{ audioUrl: string }> {
  const { data } = await apiClient.post<{ audio_url?: string; audioUrl?: string }>("/voice/speak", { text });
  return { audioUrl: resolveAudioUrl(data.audioUrl ?? data.audio_url ?? "") };
}

export const speakText = synthesizeSpeech;
