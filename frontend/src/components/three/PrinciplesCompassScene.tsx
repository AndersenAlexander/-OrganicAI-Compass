import { Html, Line, Sparkles } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { Heart, ShieldCheck, Sprout, Target, UserRoundCheck, UsersRound } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { AdditiveBlending, CatmullRomCurve3, Vector3 } from "three";
import type { Group, Mesh } from "three";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

const principleNodes = [
  { label: "Human-Centred", icon: Heart, color: "#5eead4", accent: "teal", position: [-1.74, 0.66, 0.04] },
  { label: "Trust", icon: ShieldCheck, color: "#67e8f9", accent: "cyan", position: [-0.64, 1.16, 0.02] },
  { label: "Empowerment", icon: UserRoundCheck, color: "#c4b5fd", accent: "violet", position: [0.8, 1.04, 0.06] },
  { label: "Growth", icon: Sprout, color: "#bef264", accent: "green", position: [1.78, 0.06, 0.04] },
  { label: "Collaboration", icon: UsersRound, color: "#2dd4bf", accent: "bluegreen", position: [0.74, -0.82, 0.02] },
  { label: "Purpose", icon: Target, color: "#e2c576", accent: "gold", position: [-0.92, -0.8, 0.06] },
] as const;

const compactPositions = [
  [-1.22, 0.8, 0.04],
  [-0.5, 1.2, 0.02],
  [0.66, 1.08, 0.06],
  [1.28, 0.02, 0.04],
  [0.72, -1.04, 0.02],
  [-0.76, -1.02, 0.06],
] as const;

function PrincipleNode({
  node,
  position,
  index,
  reduced,
}: {
  node: (typeof principleNodes)[number];
  position: readonly [number, number, number];
  index: number;
  reduced: boolean;
}) {
  const group = useRef<Group>(null);
  const Icon = node.icon;

  useFrame(({ clock }) => {
    if (!group.current || reduced) return;
    group.current.position.y = position[1] + Math.sin(clock.elapsedTime * 0.82 + index * 0.72) * 0.026;
  });

  return (
    <group ref={group} position={position}>
      <pointLight intensity={0.75} distance={1.35} color={node.color} />
      <mesh>
        <sphereGeometry args={[0.2, 30, 30]} />
        <meshPhysicalMaterial color={node.color} emissive={node.color} emissiveIntensity={0.8} roughness={0.18} clearcoat={1} />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.38, 28, 28]} />
        <meshPhysicalMaterial
          color="#f0fffb"
          transparent
          opacity={0.13}
          transmission={0.72}
          thickness={0.32}
          depthWrite={false}
          roughness={0.08}
          clearcoat={1}
        />
      </mesh>
      <Html center distanceFactor={4.8}>
        <span className={`principles-compass-node-label accent-${node.accent}`}>
          <span className="principles-compass-node-icon">
            <Icon size={17} />
          </span>
          <b>{node.label}</b>
        </span>
      </Html>
    </group>
  );
}

function CompassNeedle({ rotation = 0 }: { rotation?: number }) {
  return (
    <group rotation={[0, 0, rotation]}>
      <mesh position={[0, 0.32, 0.58]} rotation={[0, 0, Math.PI]}>
        <coneGeometry args={[0.052, 0.62, 4]} />
        <meshStandardMaterial color="#f8fafc" emissive="#5eead4" emissiveIntensity={0.58} transparent opacity={0.84} />
      </mesh>
      <mesh position={[0, -0.28, 0.58]}>
        <coneGeometry args={[0.045, 0.52, 4]} />
        <meshStandardMaterial color="#e2c576" emissive="#84cc16" emissiveIntensity={0.34} transparent opacity={0.66} />
      </mesh>
    </group>
  );
}

function ConstitutionalOrb({ reduced }: { reduced: boolean }) {
  const orb = useRef<Group>(null);
  const inner = useRef<Mesh>(null);

  useFrame((_, delta) => {
    if (reduced) return;
    if (orb.current) orb.current.rotation.y += delta * 0.08;
    if (inner.current) inner.current.rotation.x += delta * 0.055;
  });

  return (
    <group ref={orb} position={[0, 0, -0.08]}>
      <mesh>
        <sphereGeometry args={[1.08, 80, 80]} />
        <meshPhysicalMaterial
          color="#eafffb"
          transparent
          transmission={0.94}
          thickness={0.86}
          roughness={0.05}
          clearcoat={1}
          clearcoatRoughness={0.03}
          ior={1.38}
          opacity={0.36}
          depthWrite={false}
        />
      </mesh>
      <mesh ref={inner}>
        <icosahedronGeometry args={[0.82, 3]} />
        <meshBasicMaterial color="#7dd3fc" wireframe transparent opacity={0.1} depthWrite={false} />
      </mesh>
      <mesh>
        <sphereGeometry args={[0.72, 56, 56]} />
        <meshBasicMaterial color="#2dd4bf" transparent opacity={0.17} blending={AdditiveBlending} depthWrite={false} />
      </mesh>
      <group rotation={[0, 0, -0.4]}>
        <CompassNeedle />
        <CompassNeedle rotation={Math.PI / 2} />
      </group>
      <Html center>
        <div className="principles-compass-core-label">
          <b>HUMAN</b>
          <span>+</span>
          <b>AI</b>
        </div>
      </Html>
    </group>
  );
}

function PrinciplesWorld({ compact, reduced }: { compact: boolean; reduced: boolean }) {
  const world = useRef<Group>(null);
  const orbit = useRef<Group>(null);
  const energy = useRef<Mesh>(null);
  const positions = useMemo(
    () => principleNodes.map((node, index) => new Vector3(...(compact ? compactPositions[index] : node.position))),
    [compact]
  );
  const curve = useMemo(() => new CatmullRomCurve3(positions, true, "centripetal"), [positions]);
  const pathPoints = useMemo(() => curve.getPoints(160), [curve]);

  useFrame(({ clock }, delta) => {
    if (!reduced) {
      if (world.current) {
        world.current.rotation.y = Math.sin(clock.elapsedTime * 0.16) * 0.055;
        world.current.position.y = Math.sin(clock.elapsedTime * 0.32) * 0.018;
      }
      if (orbit.current) orbit.current.rotation.z += delta * 0.016;
    }

    if (energy.current) {
      const point = curve.getPointAt(reduced ? 0.08 : (clock.elapsedTime * 0.035) % 1);
      energy.current.position.copy(point);
    }
  });

  return (
    <group ref={world} scale={compact ? 0.98 : 0.98} position={compact ? [0, -0.02, 0] : [0.08, 0.12, 0]}>
      <Sparkles
        count={compact ? 28 : 52}
        scale={compact ? [3.1, 2.65, 1.75] : [4.6, 2.8, 2]}
        size={compact ? 0.52 : 0.64}
        speed={reduced ? 0 : 0.05}
        opacity={compact ? 0.15 : 0.18}
        color="#d8fffa"
      />

      {positions.map((position, index) => (
        <Line
          key={`connection-${principleNodes[index].label}`}
          points={[position, new Vector3(0, 0, -0.08)]}
          color={principleNodes[index].color}
          transparent
          opacity={0.3}
          lineWidth={0.75}
        />
      ))}

      <Line points={pathPoints} color="#5eead4" transparent opacity={0.58} lineWidth={1.05} />
      <mesh ref={energy}>
        <sphereGeometry args={[0.055, 22, 22]} />
        <meshBasicMaterial color="#eafffb" transparent opacity={0.88} blending={AdditiveBlending} depthWrite={false} />
      </mesh>

      <group ref={orbit} position={[0, 0, -0.08]}>
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[1.18, 0.0035, 10, 180]} />
          <meshBasicMaterial color="#2dd4bf" transparent opacity={0.18} blending={AdditiveBlending} depthWrite={false} />
        </mesh>
        <mesh rotation={[0.72, 0.12, 0.7]}>
          <torusGeometry args={[1.34, 0.0035, 10, 180]} />
          <meshBasicMaterial color="#38bdf8" transparent opacity={0.16} blending={AdditiveBlending} depthWrite={false} />
        </mesh>
        <mesh rotation={[-0.78, 0.74, 0.18]}>
          <torusGeometry args={[1.48, 0.0035, 10, 180]} />
          <meshBasicMaterial color="#84cc16" transparent opacity={0.13} blending={AdditiveBlending} depthWrite={false} />
        </mesh>
      </group>

      <ConstitutionalOrb reduced={reduced} />
      {principleNodes.map((node, index) => (
        <PrincipleNode
          key={node.label}
          node={node}
          position={compact ? compactPositions[index] : node.position}
          index={index}
          reduced={reduced}
        />
      ))}
    </group>
  );
}

function PrinciplesCompassCssFallback() {
  return (
    <div className="principles-compass-fallback" role="img" aria-label="Six OrganicAI principles orbiting a HUMAN plus AI sphere">
      <div className="principles-fallback-core">
        <b>HUMAN</b>
        <span>+</span>
        <b>AI</b>
      </div>
      {principleNodes.map((node, index) => {
        const Icon = node.icon;
        return (
          <span key={node.label} className={`principles-fallback-node node-${index}`}>
            <Icon size={16} aria-hidden="true" />
            <b>{node.label}</b>
          </span>
        );
      })}
    </div>
  );
}

export function PrinciplesCompassScene() {
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

  if (!webgl) return <PrinciplesCompassCssFallback />;

  return (
    <div className="principles-compass-canvas">
      <Canvas
        aria-hidden
        dpr={[1, 1.5]}
        camera={{ position: [0, 0, compact ? 6.3 : 6.45], fov: compact ? 38 : 35 }}
        gl={{ alpha: true, antialias: true, powerPreference: "high-performance" }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.58} />
        <directionalLight position={[-4, 4, 5]} intensity={1.05} color="#effffc" />
        <pointLight position={[2.4, 1.4, 2.7]} intensity={2.25} color="#22d3ee" />
        <pointLight position={[-2.1, -1.2, 2.4]} intensity={1.45} color="#a3e635" />
        <pointLight position={[0.2, 0.1, 2.8]} intensity={1.2} color="#f8fafc" />
        <PrinciplesWorld compact={compact} reduced={reduced} />
      </Canvas>
    </div>
  );
}
