import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import type { Mesh } from "three";

type FloatingOrbProps = {
  position?: [number, number, number];
  color?: string;
  scale?: number;
};

export function FloatingOrb({ position = [0, 0, 0], color = "#5eead4", scale = 1 }: FloatingOrbProps) {
  const ref = useRef<Mesh>(null);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.position.y = position[1] + Math.sin(clock.elapsedTime * 0.8 + position[0]) * 0.08;
    ref.current.rotation.y += 0.006;
  });

  return (
    <mesh ref={ref} position={position} scale={scale}>
      <sphereGeometry args={[0.34, 32, 32]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} roughness={0.26} metalness={0.18} transparent opacity={0.78} />
    </mesh>
  );
}
