import { useContext } from "react";
import { LiveVoiceContext } from "../context/LiveVoiceContext";

export function useLiveVoice() {
  const context = useContext(LiveVoiceContext);
  if (!context) throw new Error("useLiveVoice must be used within LiveVoiceProvider");
  return context;
}
