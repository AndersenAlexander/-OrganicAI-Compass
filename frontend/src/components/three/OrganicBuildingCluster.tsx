export function OrganicBuildingCluster() {
  const buildings: Array<[number, number, number, number]> = [
    [-2.5, -1.15, -0.8, 0.75],
    [-1.7, -1.05, -1.1, 1.05],
    [1.8, -1.08, -1.0, 0.95],
    [2.6, -1.18, -0.6, 0.66],
  ];

  return (
    <group>
      {buildings.map(([x, y, z, height], index) => (
        <mesh key={index} position={[x, y + height / 2, z]}>
          <cylinderGeometry args={[0.22, 0.36, height, 8]} />
          <meshStandardMaterial color="#dffcf7" emissive="#2dd4bf" emissiveIntensity={0.08} roughness={0.48} metalness={0.2} transparent opacity={0.72} />
        </mesh>
      ))}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.15, 0]}>
        <torusGeometry args={[2.5, 0.012, 12, 120]} />
        <meshBasicMaterial color="#5eead4" transparent opacity={0.5} />
      </mesh>
    </group>
  );
}
