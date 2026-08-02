import { apiClient, AUTH_TOKEN_KEY } from "./client";
import type { AuthUser } from "../types/auth";
export type DemoLoginResponse={access_token:string;token_type:"bearer";active_profile_id:string;user:AuthUser & {is_demo:true}};
export type DemoResetResponse={status:"reset";active_profile_id:string;message:string};
export async function loginDemo(){const {data}=await apiClient.post<DemoLoginResponse>("/demo/login");localStorage.setItem(AUTH_TOKEN_KEY,data.access_token);localStorage.setItem("organicai_active_profile_id",data.active_profile_id);return data}
export async function resetDemoData(){return (await apiClient.post<DemoResetResponse>("/demo/reset")).data}
