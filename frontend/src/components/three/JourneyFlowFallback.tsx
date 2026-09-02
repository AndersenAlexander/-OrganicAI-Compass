const fallbackNodes = ["Intention", "Diagnostic", "Potential Map", "AI Coach", "Roadmap", "Growth"];

export function JourneyFlowFallback() {
  return (
    <div className="journey-flow-fallback" role="img" aria-label="Six-stage OrganicAI journey flow">
      <span className="journey-flow-path" />
      <div className="journey-flow-core">
        <b>HUMAN</b>
        <span>+</span>
        <b>AI</b>
      </div>
      {fallbackNodes.map((node, index) => (
        <span className={`journey-flow-fallback-node node-${index}`} key={node}>
          <b>{String(index + 1).padStart(2, "0")}</b>
          {node}
        </span>
      ))}
    </div>
  );
}
