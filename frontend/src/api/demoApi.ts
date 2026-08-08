import { apiClient, AUTH_TOKEN_KEY } from "./client";
import type { AuthUser } from "../types/auth";
export type DemoLoginResponse={access_token:string;token_type:"bearer";active_profile_id:string;demo_mode:true;user:AuthUser & {is_demo:true}};
export type DemoResetResponse={ok:true;status:"reset";profile_id:string;active_profile_id:string;reset_sections:string[];message:string};
export async function loginDemo(){const {data}=await apiClient.post<DemoLoginResponse>("/auth/demo-login");localStorage.setItem(AUTH_TOKEN_KEY,data.access_token);localStorage.setItem("organicai_active_profile_id",data.active_profile_id);return data}
export async function resetDemoData(){return (await apiClient.post<DemoResetResponse>("/demo/reset")).data}
