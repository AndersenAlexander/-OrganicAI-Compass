function Figure({ x, color, emissive }: { x: number; color: string; emissive: string }) {
  return (
    <group position={[x, -0.55, 0]}>
      <mesh position={[0, 0.78, 0]}>
        <sphereGeometry args={[0.16, 24, 24]} />
        <meshStandardMaterial color={color} emissive={emissive} emissiveIntensity={0.18} />
      </mesh>
      <mesh position={[0, 0.25, 0]}>
        <capsuleGeometry args={[0.16, 0.65, 8, 16]} />
        <meshStandardMaterial color={color} emissive={emissive} emissiveIntensity={0.16} roughness={0.38} />
      </mesh>
    </group>
  );
}

export function HumanAIFigures3D() {
  return (
    <group>
      <Figure x={-1.15} color="#f8fafc" emissive="#84cc16" />
      <Figure x={1.15} color="#dbeafe" emissive="#38bdf8" />
      <mesh rotation={[0, 0, Math.PI / 2]} position={[0, 0, 0]}>
        <torusGeometry args={[1.18, 0.01, 8, 160]} />
        <meshBasicMaterial color="#99f6e4" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}
