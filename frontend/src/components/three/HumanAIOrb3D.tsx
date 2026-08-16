import { Html, Sparkles } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Group, Mesh } from "three";

function CompassNeedle({ rotation = 0 }: { rotation?: number }) {
  return (
    <group rotation={[0, 0, rotation]}>
      <mesh position={[0, 0.42, 0]} rotation={[0, 0, Math.PI]}>
        <coneGeometry args={[0.09, 0.58, 4]} />
        <meshStandardMaterial color="#eafffb" emissive="#5eead4" emissiveIntensity={0.8} transparent opacity={0.88} />
      </mesh>
      <mesh position={[0, -0.42, 0]}>
        <coneGeometry args={[0.09, 0.58, 4]} />
        <meshStandardMaterial color="#eafffb" emissive="#5eead4" emissiveIntensity={0.55} transparent opacity={0.72} />
      </mesh>
    </group>
  );
}

function OrbScene() {
  const group = useRef<Group>(null);
  const compass = useRef<Group>(null);
  const ringA = useRef<Mesh>(null);
  const ringB = useRef<Mesh>(null);
  const ringC = useRef<Mesh>(null);
  const sphere = useRef<Mesh>(null);

  useFrame(({ clock }, delta) => {
    const t = clock.elapsedTime;
    if (group.current) {
      group.current.rotation.y += delta * 0.1;
      group.current.position.y = Math.sin(t * 0.65) * 0.03;
      const pulse = 1.002 + Math.sin(t * 1.0) * 0.013;
      group.current.scale.setScalar(pulse);
    }
    if (compass.current) compass.current.rotation.z += delta * 0.12;
    if (ringA.current) ringA.current.rotation.z += delta * 0.1;
    if (ringB.current) ringB.current.rotation.x -= delta * 0.08;
    if (ringC.current) ringC.current.rotation.y += delta * 0.06;
    if (sphere.current) sphere.current.rotation.y -= delta * 0.06;
  });

  return (
    <group ref={group}>
      <mesh ref={sphere}>
        <sphereGeometry args={[1.05, 64, 64]} />
        <meshPhysicalMaterial
          color="#b7f7eb"
          emissive="#2dd4bf"
          emissiveIntensity={0.12}
          roughness={0.07}
          metalness={0}
          transmission={0.9}
          thickness={0.7}
          ior={1.35}
          clearcoat={1}
          clearcoatRoughness={0.05}
          transparent
          opacity={0.38}
          depthWrite={false}
        />
      </mesh>

      <mesh ref={ringA} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.24, 0.018, 16, 180]} />
        <meshStandardMaterial color="#22d3ee" emissive="#22d3ee" emissiveIntensity={1.25} transparent opacity={0.82} />
      </mesh>
      <mesh ref={ringB} rotation={[0.68, 0.15, 0.35]}>
        <torusGeometry args={[1.16, 0.014, 16, 180]} />
        <meshStandardMaterial color="#2dd4bf" emissive="#2dd4bf" emissiveIntensity={0.9} transparent opacity={0.62} />
      </mesh>
      <mesh ref={ringC} rotation={[0.1, Math.PI / 2, 0.2]}>
        <torusGeometry args={[1.0, 0.012, 16, 180]} />
        <meshStandardMaterial color="#a3e635" emissive="#84cc16" emissiveIntensity={0.7} transparent opacity={0.48} />
      </mesh>

      <group ref={compass}>
        <CompassNeedle />
        <CompassNeedle rotation={Math.PI / 2} />
        <mesh>
          <sphereGeometry args={[0.13, 32, 32]} />
          <meshStandardMaterial color="#ffffff" emissive="#99f6e4" emissiveIntensity={1.2} />
        </mesh>
      </group>

      <Sparkles count={38} scale={2.55} size={1.55} speed={0.18} opacity={0.58} color="#dffcf7" />
      <Html center transform={false} zIndexRange={[10, 0]}>
        <div className="human-ai-orb-html">
          HUMAN
          <br />+<br />
          AI
        </div>
      </Html>
    </group>
  );
}

export function HumanAIOrb3D() {
  return (
    <Canvas aria-hidden="true" camera={{ position: [0, 0, 4.4], fov: 42 }} dpr={[1, 1.6]} gl={{ alpha: true, antialias: true }}>
      <ambientLight intensity={0.6} />
      <directionalLight position={[-3, 4, 4]} intensity={1.05} color="#ffffff" />
      <pointLight position={[0, 0.4, 2.6]} intensity={2.2} color="#5eead4" />
      <pointLight position={[-1.8, 1.5, 1.2]} intensity={1.05} color="#84cc16" />
      <pointLight position={[0.8, -0.2, 2.4]} intensity={1.1} color="#ffffff" />
      <OrbScene />
    </Canvas>
  );
}
