import { Sparkles } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { demoLoginFailureMessage } from "../api/demoApi";
import { Card } from "../components/shared/Card";
import { Button } from "../components/shared/Button";
export function DemoPage(){const {loginDemo}=useAuth();const navigate=useNavigate();const [loading,setLoading]=useState(false);const [error,setError]=useState("");async function enter(){setLoading(true);setError("");try{navigate(`/profile/${await loginDemo()}`)}catch(error){setError(demoLoginFailureMessage(error))}finally{setLoading(false)}}return <div className="mx-auto max-w-2xl py-12"><Card className="space-y-5"><Sparkles className="text-teal"/><p className="text-sm font-bold tracking-[.15em] text-teal">ORGANICAI DEMO</p><h1 className="font-display text-5xl font-bold text-navy">Explore a completed OrganicAI journey</h1><p className="text-slate-600">The demo includes a completed human diagnostic, Human Potential Map, AI Coach conversations, personalized roadmap, progress indicators, grounded sources, and report preview.</p>{error&&<p className="text-sm text-red-600">{error}</p>}<Button onClick={()=>void enter()} disabled={loading}>{loading?"Preparing demo...":"Enter OrganicAI Demo"}</Button></Card></div>}
