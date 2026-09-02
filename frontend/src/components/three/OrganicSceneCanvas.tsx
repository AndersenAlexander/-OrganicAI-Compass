import { Canvas, useFrame } from "@react-three/fiber";
import { Suspense, useRef } from "react";
import type { Group } from "three";
import { FloatingOrb } from "./FloatingOrb";
import { HumanAIFigures3D } from "./HumanAIFigures3D";
import { OrganicBuildingCluster } from "./OrganicBuildingCluster";
import { OrganicParticleField } from "./OrganicParticleField";

function Scene() {
  const group = useRef<Group>(null);

  useFrame(({ clock }) => {
    if (!group.current) return;
    group.current.rotation.y = Math.sin(clock.elapsedTime * 0.25) * 0.05;
  });

  return (
    <group ref={group}>
      <OrganicParticleField />
      <OrganicBuildingCluster />
      <HumanAIFigures3D />
      <FloatingOrb position={[0, 0.2, 0]} scale={1.2} />
      <FloatingOrb position={[-2.2, 0.65, -0.8]} color="#84cc16" scale={0.7} />
      <FloatingOrb position={[2.2, 0.85, -0.7]} color="#38bdf8" scale={0.7} />
    </group>
  );
}

export function OrganicSceneCanvas({ className = "" }: { className?: string }) {
  return (
    <div className={className}>
      <Canvas camera={{ position: [0, 1.0, 6.4], fov: 42 }} dpr={[1, 1.5]}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[3, 5, 4]} intensity={1.4} />
        <pointLight position={[0, 1, 2]} intensity={3} color="#5eead4" />
        <pointLight position={[-3, 1, 1]} intensity={1.2} color="#84cc16" />
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
    </div>
  );
}
