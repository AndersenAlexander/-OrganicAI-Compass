import { ConceptMapBlock } from "./ConceptMapBlock";

export function StudioCanvas() {
  const blocks = ["Talent Map Visual", "Fear Transformation Map", "Human-AI Collaboration Map", "Project Concept Board", "Future Self Board"];
  return <div className="grid gap-4 rounded-[2rem] border border-white/80 bg-white/55 p-5 md:grid-cols-2">{blocks.map((block) => <ConceptMapBlock key={block} title={block} />)}</div>;
}
