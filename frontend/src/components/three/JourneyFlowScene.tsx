import { Html, Line, Sparkles } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { BrainCircuit, Headphones, Map, Network, Sprout, Target } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AdditiveBlending, CatmullRomCurve3, Vector3 } from "three";
import type { Group, Mesh } from "three";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";
import { JourneyFlowFallback } from "./JourneyFlowFallback";

const stageNodes = [
  { number: "01", label: "Intention", icon: Target, color: "#5eead4", position: [-1.86, 0.98, 0.02] },
  { number: "02", label: "Diagnostic", icon: BrainCircuit, color: "#67e8f9", position: [-2.42, 0.04, 0.08] },
  { number: "03", label: "Potential Map", icon: Network, color: "#bef264", position: [-1.36, -0.94, 0] },
  { number: "04", label: "AI Coach", icon: Headphones, color: "#c4b5fd", position: [1.34, -0.94, 0.06] },
  { number: "05", label: "Roadmap", icon: Map, color: "#d9f99d", position: [2.38, 0.04, 0] },
  { number: "06", label: "Growth", icon: Sprout, color: "#a3e635", position: [1.84, 0.98, 0.06] },
] as const;

function StageNode({ node }: { node: (typeof stageNodes)[number] }) {
  const Icon = node.icon;
  const position = node.position as [number, number, number];

  return (
    <group position={position}>
      <pointLight intensity={0.95} distance={1.6} color={node.color} />
      <Line
        points={[
          [0, 0, 0],
          [0, -0.28, -0.02],
        ]}
        color={node.color}
        transparent
        opacity={0.32}
        lineWidth={0.7}
      />
      <mesh>
        <sphereGeometry args={[0.16, 30, 30]} />
        <meshPhysicalMaterial
          color={node.color}
          emissive={node.color}
          emissiveIntensity={0.62}
          roughness={0.18}
          clearcoat={1}
        />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.28, 30, 30]} />
        <meshPhysicalMaterial
          color="#f0fffb"
          transparent
          opacity={0.12}
          transmission={0.7}
          thickness={0.35}
          depthWrite={false}
          roughness={0.06}
          clearcoat={1}
        />
      </mesh>
      <Html center distanceFactor={4.5}>
        <span className="journey-flow-node-label">
          <b>{node.number}</b>
          <span className="journey-flow-node-icon">
            <Icon size={16} />
          </span>
          <small>{node.label}</small>
        </span>
      </Html>
    </group>
  );
}

const compactStagePositions = [
  [-1.18, 0.96, 0.02],
  [-1.52, 0.02, 0.08],
  [-0.96, -1.04, 0],
  [0.96, -1.04, 0.06],
  [1.52, 0.02, 0],
  [1.18, 0.96, 0.06],
] as const;

function ResponsiveStageNode({ node, compact, index }: { node: (typeof stageNodes)[number]; compact: boolean; index: number }) {
  const responsiveNode = compact
    ? { ...node, position: compactStagePositions[index] }
    : node;

  return <StageNode node={responsiveNode as (typeof stageNodes)[number]} />;
}

function CentralCompassOrb({ reduced }: { reduced: boolean }) {
  const orb = useRef<Group>(null);

  useFrame((_, delta) => {
    if (orb.current && !reduced) orb.current.rotation.y += delta * 0.08;
  });

  return (
    <group ref={orb} position={[0.05, 0.02, -0.1]}>
      <mesh>
        <sphereGeometry args={[0.94, 80, 80]} />
        <meshPhysicalMaterial
          color="#eafffb"
          transparent
          transmission={0.94}
          thickness={0.9}
          roughness={0.05}
          metalness={0.02}
          clearcoat={1}
          clearcoatRoughness={0.03}
          ior={1.38}
          opacity={0.32}
          depthWrite={false}
        />
      </mesh>
      <mesh>
        <icosahedronGeometry args={[0.72, 3]} />
        <meshBasicMaterial color="#7dd3fc" wireframe transparent opacity={0.1} depthWrite={false} />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.68, 56, 56]} />
        <meshBasicMaterial color="#2dd4bf" transparent opacity={0.18} blending={AdditiveBlending} depthWrite={false} />
      </mesh>
      <group rotation={[0, 0, -0.46]}>
        <mesh position={[0, 0.29, 0.54]} rotation={[0, 0, Math.PI]}>
          <coneGeometry args={[0.05, 0.64, 4]} />
          <meshStandardMaterial color="#f0fffb" emissive="#5eead4" emissiveIntensity={0.56} transparent opacity={0.82} />
        </mesh>
        <mesh position={[0, -0.27, 0.54]}>
          <coneGeometry args={[0.044, 0.56, 4]} />
          <meshStandardMaterial color="#e2c576" emissive="#a3e635" emissiveIntensity={0.32} transparent opacity={0.62} />
        </mesh>
      </group>
      <Html center>
        <div className="journey-flow-core-label">
          <b>HUMAN</b>
          <span>+</span>
          <b>AI</b>
        </div>
      </Html>
    </group>
  );
}

function JourneyWorld({ reduced, compact }: { reduced: boolean; compact: boolean }) {
  const world = useRef<Group>(null);
  const rings = useRef<Group>(null);
  const energy = useRef<Mesh>(null);
  const nodePositions = useMemo(
    () => stageNodes.map((node, index) => new Vector3(...(compact ? compactStagePositions[index] : node.position))),
    [compact]
  );
  const curve = useMemo(
    () => new CatmullRomCurve3(nodePositions, true, "centripetal"),
    [nodePositions]
  );
  const pathPoints = useMemo(() => curve.getPoints(120), [curve]);

  useFrame(({ clock }, delta) => {
    if (world.current && !reduced) {
      world.current.rotation.y = Math.sin(clock.elapsedTime * 0.18) * 0.06;
      world.current.position.y = Math.sin(clock.elapsedTime * 0.35) * 0.025;
    }
    if (rings.current && !reduced) rings.current.rotation.z += delta * 0.025;
    if (energy.current) {
      const point = curve.getPointAt(reduced ? 0.08 : (clock.elapsedTime * 0.065) % 1);
      energy.current.position.copy(point);
    }
  });

  return (
    <group ref={world} scale={compact ? 1 : 1.08} position={compact ? [0, -0.02, 0] : [0.08, -0.02, 0]}>
      <Sparkles
        count={compact ? 34 : 72}
        scale={compact ? [3.3, 2.7, 1.8] : [5.4, 3.1, 2.2]}
        size={compact ? 0.55 : 0.68}
        speed={reduced ? 0 : 0.06}
        opacity={compact ? 0.18 : 0.22}
        color="#d8fffa"
      />
      <Line points={pathPoints} color="#5eead4" transparent opacity={0.62} lineWidth={1.1} />
      <mesh ref={energy}>
        <sphereGeometry args={[0.055, 22, 22]} />
        <meshBasicMaterial color="#eafffb" transparent opacity={0.95} blending={AdditiveBlending} depthWrite={false} />
      </mesh>
      <group ref={rings} position={[0.05, 0.02, -0.1]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[1.05, 0.0035, 10, 180]} />
          <meshBasicMaterial color="#2dd4bf" transparent opacity={0.2} blending={AdditiveBlending} depthWrite={false} />
        </mesh>
        <mesh rotation={[0.72, 0.12, 0.7]}>
          <torusGeometry args={[1.19, 0.0035, 10, 180]} />
          <meshBasicMaterial color="#38bdf8" transparent opacity={0.18} blending={AdditiveBlending} depthWrite={false} />
        </mesh>
        <mesh rotation={[-0.78, 0.74, 0.18]}>
          <torusGeometry args={[1.33, 0.0035, 10, 180]} />
          <meshBasicMaterial color="#84cc16" transparent opacity={0.14} blending={AdditiveBlending} depthWrite={false} />
        </mesh>
      </group>
      <CentralCompassOrb reduced={reduced} />
      {stageNodes.map((node, index) => (
        <ResponsiveStageNode key={node.label} node={node} compact={compact} index={index} />
      ))}
    </group>
  );
}

export function JourneyFlowScene() {
  const reduced = useReducedMotionPreference();
  const [webgl, setWebgl] = useState(true);
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    try {
      const canvas = document.createElement("canvas");
      setWebgl(Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl")));
    } catch {
      setWebgl(false);
    }
  }, []);

  useEffect(() => {
    const updateCompact = () => setCompact(window.innerWidth < 900);
    updateCompact();
    window.addEventListener("resize", updateCompact);
    return () => window.removeEventListener("resize", updateCompact);
  }, []);

  if (!webgl) return <JourneyFlowFallback />;

  return (
    <div className="journey-flow-canvas">
      <Canvas
        aria-hidden
        dpr={[1, 1.5]}
        camera={{ position: [0, 0, compact ? 6.35 : 6.2], fov: compact ? 38 : 36 }}
        gl={{
          alpha: true,
          antialias: true,
          powerPreference: "high-performance",
        }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.56} />
        <directionalLight position={[-4, 4, 5]} intensity={1.1} color="#effffc" />
        <pointLight position={[2.4, 1.4, 2.7]} intensity={2.4} color="#22d3ee" />
        <pointLight position={[-2.1, -1.2, 2.4]} intensity={1.55} color="#a3e635" />
        <JourneyWorld reduced={reduced} compact={compact} />
      </Canvas>
    </div>
  );
}
