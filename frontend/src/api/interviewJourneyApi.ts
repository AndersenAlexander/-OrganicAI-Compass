import { apiClient } from "./client";
import type {
  AnswerBuilder,
  FollowUpDraft,
  Interview,
  InterviewDashboard,
  InterviewQuestion,
  InterviewReflection,
  MockInterviewSession,
  OfferReview,
  PreparationBrief,
  StarStory,
  VoiceStatus,
} from "../types/interviewJourney";

export async function getInterviewDashboard(profileId: string) {
  const { data } = await apiClient.get<InterviewDashboard>(`/v1/profiles/${profileId}/interviews/dashboard`);
  return data;
}

export async function getInterviews(profileId: string) {
  const { data } = await apiClient.get<Interview[]>(`/v1/profiles/${profileId}/interviews`);
  return data;
}

export async function createInterview(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<Interview>(`/v1/profiles/${profileId}/interviews`, payload);
  return data;
}

export async function getInterview(interviewId: string) {
  const { data } = await apiClient.get<Interview>(`/v1/interviews/${interviewId}`);
  return data;
}

export async function updateInterview(interviewId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.put<Interview>(`/v1/interviews/${interviewId}`, payload);
  return data;
}

export async function createPreparationBrief(interviewId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<PreparationBrief>(`/v1/interviews/${interviewId}/preparation`, payload);
  return data;
}

export async function getPreparationBrief(interviewId: string) {
  const { data } = await apiClient.get<PreparationBrief | null>(`/v1/interviews/${interviewId}/preparation`);
  return data;
}

export async function generateInterviewQuestions(interviewId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<{ interview_id: string; questions: InterviewQuestion[]; generated: boolean }>(`/v1/interviews/${interviewId}/questions/generate`, payload);
  return data;
}

export async function getInterviewQuestions(interviewId: string) {
  const { data } = await apiClient.get<InterviewQuestion[]>(`/v1/interviews/${interviewId}/questions`);
  return data;
}

export async function saveInterviewQuestion(questionId: string, saved = true) {
  const { data } = await apiClient.post<InterviewQuestion>(`/v1/interview-questions/${questionId}/save`, { saved });
  return data;
}

export async function buildInterviewAnswer(questionId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<AnswerBuilder>(`/v1/interview-questions/${questionId}/answer`, payload);
  return data;
}

export async function getStarStories(profileId: string) {
  const { data } = await apiClient.get<StarStory[]>(`/v1/profiles/${profileId}/star-stories`);
  return data;
}

export async function createStarStory(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<StarStory>(`/v1/profiles/${profileId}/star-stories`, payload);
  return data;
}

export async function evaluateStarStory(storyId: string) {
  const { data } = await apiClient.post<StarStory>(`/v1/star-stories/${storyId}/evaluate`);
  return data;
}

export async function createMockSession(interviewId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<MockInterviewSession>(`/v1/interviews/${interviewId}/mock-sessions`, payload);
  return data;
}

export async function getMockSessions(interviewId: string) {
  const { data } = await apiClient.get<MockInterviewSession[]>(`/v1/interviews/${interviewId}/mock-sessions`);
  return data;
}

export async function startMockSession(sessionId: string) {
  const { data } = await apiClient.post<MockInterviewSession>(`/v1/mock-sessions/${sessionId}/start`);
  return data;
}

export async function addMockTurn(sessionId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post(`/v1/mock-sessions/${sessionId}/turns`, payload);
  return data;
}

export async function completeMockSession(sessionId: string, payload: Record<string, unknown> = {}) {
  const { data } = await apiClient.post<MockInterviewSession>(`/v1/mock-sessions/${sessionId}/complete`, payload);
  return data;
}

export async function getInterviewVoiceStatus() {
  const { data } = await apiClient.get<VoiceStatus>("/v1/interview-voice/status");
  return data;
}

export async function createReflection(interviewId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<InterviewReflection>(`/v1/interviews/${interviewId}/reflection`, payload);
  return data;
}

export async function getReflection(interviewId: string) {
  const { data } = await apiClient.get<InterviewReflection | null>(`/v1/interviews/${interviewId}/reflection`);
  return data;
}

export async function createFollowUpDraft(interviewId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<FollowUpDraft>(`/v1/interviews/${interviewId}/follow-up-drafts`, payload);
  return data;
}

export async function getFollowUpDrafts(interviewId: string) {
  const { data } = await apiClient.get<FollowUpDraft[]>(`/v1/interviews/${interviewId}/follow-up-drafts`);
  return data;
}

export async function recordInterviewApplicationEvent(interviewId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post(`/v1/interviews/${interviewId}/application-events`, payload);
  return data;
}

export async function getOfferReviews(profileId: string) {
  const { data } = await apiClient.get<OfferReview[]>(`/v1/profiles/${profileId}/offer-reviews`);
  return data;
}

export async function createOfferReview(profileId: string, payload: Record<string, unknown>) {
  const { data } = await apiClient.post<OfferReview>(`/v1/profiles/${profileId}/offer-reviews`, payload);
  return data;
}
