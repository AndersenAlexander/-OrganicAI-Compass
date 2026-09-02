import { Points, PointMaterial } from "@react-three/drei";
import { useMemo } from "react";

export function OrganicParticleField({ count = 180 }: { count?: number }) {
  const positions = useMemo(() => {
    const values = new Float32Array(count * 3);
    for (let index = 0; index < count; index += 1) {
      values[index * 3] = (Math.random() - 0.5) * 8;
      values[index * 3 + 1] = (Math.random() - 0.5) * 4;
      values[index * 3 + 2] = (Math.random() - 0.5) * 5;
    }
    return values;
  }, [count]);

  return (
    <Points positions={positions} stride={3}>
      <PointMaterial transparent color="#99f6e4" size={0.035} sizeAttenuation depthWrite={false} opacity={0.55} />
    </Points>
  );
}
