import {apiClient} from "./client";
export type RagContextQuality="strong"|"partial"|"insufficient";
export type RagSource={source_id:string;id:string;document_name:string;section_title:string;excerpt:string;chunk_text?:string;similarity_score:number;score:number;rank:number;relevance_status?:string};
export type RagResult={id:string;document_name:string;section_title:string;chunk_text:string;score:number};
export type RagAnswerResponse={query:string;answer:string;rag_run_id:string;sources:RagSource[];sources_used:RagSource[];has_sources:boolean;confidence_note:string;ethical_note:string;insufficient_context:boolean;context_quality:RagContextQuality;fallback_reason?:string;retrieval_summary:{retrieved_count:number;used_count:number;highest_score:number|null;threshold:number;retrieval_duration_ms:number};suggested_actions:string[]};
export type RagFeedbackRequest={feedback_type?:"answer_usefulness"|"answer_grounding"|"source_relevance"|"confidence_clarity"|"ethical_note_clarity";rating:"helpful"|"partially_helpful"|"not_helpful"|"relevant"|"partially_relevant"|"not_relevant";reason_code?:string;comment?:string;profile_id?:string};
export type RagFeedbackResponse={id:string;rag_run_id:string;source_id?:string;feedback_type?:string;rating:string;saved:boolean};
export async function searchKnowledgeBase(query:string){return (await apiClient.get<{query:string;results:RagResult[]}>("/rag/search",{params:{query}})).data}
export async function askKnowledgeBase(query:string){return (await apiClient.post<RagAnswerResponse>("/rag/ask",{query})).data}
export async function reindexKnowledgeBase(){return (await apiClient.post<{documents:number;chunks:number}>("/rag/reindex")).data}
export async function saveRagFeedback(runId:string,payload:RagFeedbackRequest){return (await apiClient.post<RagFeedbackResponse>(`/rag/runs/${runId}/feedback`,payload)).data}
export async function saveSourceFeedback(runId:string,sourceId:string,payload:RagFeedbackRequest){return (await apiClient.post<RagFeedbackResponse>(`/rag/runs/${runId}/sources/${sourceId}/feedback`,{...payload,feedback_type:"source_relevance"})).data}
