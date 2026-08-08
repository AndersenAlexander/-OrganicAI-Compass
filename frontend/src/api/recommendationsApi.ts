import {apiClient} from "./client";import type{Recommendation,RecommendationCategory,RecommendationGeneration,RecommendationStatus}from"../types/recommendation";
export async function generateRecommendations(profileId:string,options?:{categories?:RecommendationCategory[];forceRegenerate?:boolean}){const{data}=await apiClient.post<RecommendationGeneration>("/recommendations/generate",{profile_id:profileId,categories:options?.categories||[],force_regenerate:options?.forceRegenerate||false});return data}
export async function getProfileRecommendations(profileId:string,filters?:{category?:string;status?:string;limit?:number}){const{data}=await apiClient.get<Recommendation[]>(`/recommendations/profile/${profileId}`,{params:filters});return data}
export async function getRecommendation(id:string){const{data}=await apiClient.get<Recommendation>(`/recommendations/${id}`);return data}
export async function updateRecommendation(id:string,patch:{status?:RecommendationStatus;user_feedback?:string;user_rating?:number}){const{data}=await apiClient.patch<Recommendation>(`/recommendations/${id}`,patch);return data}
export async function acceptRecommendation(id:string){const{data}=await apiClient.post<Recommendation>(`/recommendations/${id}/accept`);return data}
export async function rejectRecommendation(id:string,feedback?:{reason_code?:string;feedback_text?:string}){const{data}=await apiClient.post<Recommendation>(`/recommendations/${id}/reject`,feedback||{});return data}
export async function addRecommendationToRoadmap(id:string){const{data}=await apiClient.post(`/recommendations/${id}/add-to-roadmap`);return data}
export async function completeRecommendation(id:string){const{data}=await apiClient.post<Recommendation>(`/recommendations/${id}/complete`);return data}
export async function rateRecommendation(id:string,rating:number,feedback?:string){const{data}=await apiClient.post(`/recommendations/${id}/feedback`,{rating,feedback_text:feedback});return data}
