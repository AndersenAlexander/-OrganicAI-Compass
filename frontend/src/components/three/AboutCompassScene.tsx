import { Html, Sparkles } from "@react-three/drei";
import { Cpu, Sprout, UserRound } from "lucide-react";
import { Canvas, useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import { AdditiveBlending } from "three";
import type { Group, Mesh } from "three";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

const nodes = [
  { label: "Human", icon: UserRound, position: [0.2, 1.52, 0.2] as [number, number, number], color: "#7dd3fc" },
  { label: "AI", icon: Cpu, position: [1.68, -0.02, -0.05] as [number, number, number], color: "#38bdf8" },
  { label: "Purpose", icon: Sprout, position: [-1.55, -0.32, 0.15] as [number, number, number], color: "#bef264" },
];

function OrbitNode({ label, icon: Icon, position, color }: (typeof nodes)[number]) {
  return <group position={position}>
    <pointLight intensity={1.15} distance={1.8} color={color}/>
    <mesh><sphereGeometry args={[.16, 30, 30]}/><meshPhysicalMaterial color={color} emissive={color} emissiveIntensity={.82} roughness={.15} clearcoat={1}/></mesh>
    <mesh><sphereGeometry args={[.26, 30, 30]}/><meshPhysicalMaterial color="#eafffb" transmission={.8} thickness={.42} roughness={.06} clearcoat={1} transparent opacity={.14} depthWrite={false}/></mesh>
    <Html center distanceFactor={3.5}><span className="about-orbit-node-label"><Icon size={12}/>{label}</span></Html>
  </group>;
}

function CompassWorld({ reduced }: { reduced: boolean }) {
  const world = useRef<Group>(null); const core = useRef<Mesh>(null); const rings = useRef<Group>(null);
  useFrame(({ clock }, delta) => {
    if (reduced) return;
    if (world.current) { world.current.rotation.y += delta * .055; world.current.position.y = Math.sin(clock.elapsedTime * .45) * .05; }
    if (core.current) core.current.rotation.y -= delta * .09;
    if (rings.current) rings.current.rotation.z += delta * .025;
  });
  return <group ref={world} position={[0.28, -0.03, 0]} scale={0.86}>
    <Sparkles count={48} scale={[4.5, 3.3, 2.5]} size={.85} speed={reduced ? 0 : .08} opacity={.35} color="#d8fffa"/>
    <group ref={rings}>
      <mesh rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[1.72,.004,10,180]}/><meshBasicMaterial color="#2dd4bf" transparent opacity={.22} blending={AdditiveBlending} depthWrite={false}/></mesh>
      <mesh rotation={[.61,.05,.72]}><torusGeometry args={[1.66,.004,10,180]}/><meshBasicMaterial color="#38bdf8" transparent opacity={.2} blending={AdditiveBlending} depthWrite={false}/></mesh>
      <mesh rotation={[-.87,.78,.18]}><torusGeometry args={[1.52,.004,10,180]}/><meshBasicMaterial color="#84cc16" transparent opacity={.18} blending={AdditiveBlending} depthWrite={false}/></mesh>
    </group>
    <mesh ref={core}><sphereGeometry args={[1.12,80,80]}/><meshPhysicalMaterial color="#eafffb" transmission={.94} thickness={1} ior={1.38} roughness={.05} clearcoat={1} clearcoatRoughness={.03} metalness={.02} transparent opacity={.34} depthWrite={false}/></mesh>
    <mesh><sphereGeometry args={[.88,64,64]}/><meshBasicMaterial color="#2dd4bf" transparent opacity={.12} blending={AdditiveBlending} depthWrite={false}/></mesh>
    <mesh><icosahedronGeometry args={[.82,3]}/><meshBasicMaterial color="#7dd3fc" wireframe transparent opacity={.09} depthWrite={false}/></mesh>
    <group rotation={[0,0,-.45]}>
      <mesh position={[0,.36,.46]} rotation={[0,0,Math.PI]}><coneGeometry args={[.055,.72,4]}/><meshStandardMaterial color="#ecfffb" emissive="#5eead4" emissiveIntensity={.85} transparent opacity={.88}/></mesh>
      <mesh position={[0,-.36,.46]}><coneGeometry args={[.055,.72,4]}/><meshStandardMaterial color="#e2c576" emissive="#b9923e" emissiveIntensity={.45} transparent opacity={.68}/></mesh>
      <mesh position={[.36,0,.45]} rotation={[0,0,-Math.PI/2]}><coneGeometry args={[.04,.52,4]}/><meshStandardMaterial color="#dffcff" emissive="#38bdf8" emissiveIntensity={.55} transparent opacity={.78}/></mesh>
      <mesh position={[-.36,0,.45]} rotation={[0,0,Math.PI/2]}><coneGeometry args={[.04,.52,4]}/><meshStandardMaterial color="#dffcff" emissive="#38bdf8" emissiveIntensity={.55} transparent opacity={.78}/></mesh>
    </group>
    <Html center><div className="about-core-label"><b>HUMAN</b><span>+</span><b>AI</b></div></Html>
    {nodes.map(node => <OrbitNode key={node.label} {...node}/>)}
  </group>;
}

function Fallback() { return <div className="about-scene-fallback" role="img" aria-label="Human and AI compass"><div className="fallback-ring one"/><div className="fallback-ring two"/><div className="fallback-core"><b>HUMAN + AI</b><span>COMPASS</span></div>{nodes.map((n,i)=><span key={n.label} className={`fallback-node n${i}`}>{n.label}</span>)}</div>; }

export function AboutCompassScene() {
  const reduced = useReducedMotionPreference(); const [webgl,setWebgl]=useState(true);
  useEffect(()=>{try { const canvas=document.createElement("canvas"); setWebgl(Boolean(canvas.getContext("webgl2")||canvas.getContext("webgl"))); } catch { setWebgl(false); }},[]);
  const camera=useMemo(()=>({position:[0,0,5.8] as [number,number,number],fov:40}),[]);
  if (!webgl) return <Fallback/>;
  return <div className="about-compass-canvas"><Canvas aria-hidden camera={camera} dpr={[1,1.5]} gl={{alpha:true,antialias:true,powerPreference:"high-performance"}} style={{ background: "transparent" }}><ambientLight intensity={.55}/><directionalLight position={[-4,5,5]} intensity={1.2} color="#eafffb"/><pointLight position={[2,1,3]} intensity={3.3} color="#22d3ee"/><pointLight position={[-2,-1,2]} intensity={2.1} color="#84cc16"/><pointLight position={[0,-2,2]} intensity={1.1} color="#e2c576"/><CompassWorld reduced={reduced}/></Canvas></div>;
}
