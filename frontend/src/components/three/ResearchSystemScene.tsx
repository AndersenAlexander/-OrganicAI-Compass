import { Html, Line, Sparkles } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useEffect, useRef, useState } from "react";
import { AdditiveBlending } from "three";
import type { Group } from "three";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

const nodes = [
  { label: "PROFILE", position: [-1.15, 0.9, 0], color: "#42e8d0" },
  { label: "VALUES", position: [-1.3, -0.15, 0.08], color: "#62d9ff" },
  { label: "GOALS", position: [-0.95, -1.05, 0], color: "#8cdf3f" },
  { label: "RAG", position: [1.02, 1.08, 0.06], color: "#a78bfa" },
  { label: "COACH", position: [1.3, 0.3, 0], color: "#62d9ff" },
  { label: "VOICE", position: [1.18, -0.65, 0.08], color: "#a78bfa" },
  { label: "ACTION", position: [0.4, -1.28, 0], color: "#e5ca72" },
] as const;

function ResearchWorld({ reduced }: { reduced: boolean }) {
  const group = useRef<Group>(null);
  useFrame(({ clock }) => {
    if (group.current && !reduced) {
      group.current.rotation.y = Math.sin(clock.elapsedTime * 0.16) * 0.08;
      group.current.position.y = Math.sin(clock.elapsedTime * 0.3) * 0.025;
    }
  });

  return (
    <group ref={group}>
      <Sparkles count={42} scale={[4.8, 3.6, 2]} size={0.62} speed={reduced ? 0 : 0.05} opacity={0.2} />
      {nodes.map((node) => (
        <group key={node.label} position={node.position}>
          <Line points={[[0, 0, 0], [-node.position[0], -node.position[1], 0]]} color={node.color} opacity={0.3} transparent />
          <mesh>
            <sphereGeometry args={[0.095, 24, 24]} />
            <meshBasicMaterial color={node.color} blending={AdditiveBlending} />
          </mesh>
          <Html center distanceFactor={5.2}><span className="research-scene-node">{node.label}</span></Html>
        </group>
      ))}
      {[1.05, 1.48, 1.92].map((radius, index) => (
        <mesh key={radius} rotation={[index === 1 ? 0.65 : Math.PI / 2, index * 0.25, index * 0.5]}>
          <torusGeometry args={[radius, 0.006, 10, 160]} />
          <meshBasicMaterial color={["#42e8d0", "#a78bfa", "#8cdf3f"][index]} transparent opacity={0.25} />
        </mesh>
      ))}
      <mesh>
        <sphereGeometry args={[0.83, 56, 56]} />
        <meshPhysicalMaterial color="#d9fffa" transparent transmission={0.92} opacity={0.34} roughness={0.08} thickness={0.8} depthWrite={false} />
      </mesh>
      <mesh>
        <icosahedronGeometry args={[0.6, 2]} />
        <meshBasicMaterial color="#62d9ff" wireframe transparent opacity={0.13} />
      </mesh>
      <Html center><div className="research-scene-core"><b>HUMAN</b><span>context + agency</span></div></Html>
    </group>
  );
}

export function ResearchSystemFallback() {
  return (
    <div className="research-scene-fallback" role="img" aria-label="Human context connected to AI guidance and evaluation">
      <div className="research-fallback-ring ring-one" /><div className="research-fallback-ring ring-two" />
      <div className="research-fallback-core"><b>HUMAN</b><span>context + agency</span></div>
      {nodes.map((node, index) => <span className={`research-fallback-node node-${index}`} key={node.label}>{node.label}</span>)}
    </div>
  );
}

export function ResearchSystemScene() {
  const reduced = useReducedMotionPreference();
  const [webgl, setWebgl] = useState(true);
  useEffect(() => {
    try { const canvas = document.createElement("canvas"); setWebgl(Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"))); }
    catch { setWebgl(false); }
  }, []);
  if (!webgl) return <ResearchSystemFallback />;
  return (
    <Canvas aria-label="Research system: human context, AI processing, grounded action, and evaluation" role="img" dpr={[1, 1.5]} camera={{ position: [0, 0, 5.7], fov: 39 }} gl={{ alpha: true, antialias: true }} style={{ background: "transparent" }}>
      <ambientLight intensity={0.7} /><pointLight position={[2, 2, 3]} intensity={2} color="#62d9ff" /><pointLight position={[-2, -1, 2]} intensity={1.4} color="#8cdf3f" />
      <ResearchWorld reduced={reduced} />
    </Canvas>
  );
}
