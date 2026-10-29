'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  VolumeX, 
  Maximize2, 
  Sparkles, 
  ShieldCheck, 
  Cpu, 
  Terminal, 
  CheckCircle2,
  ChevronRight,
  Info
} from 'lucide-react';

interface AgentNodeDef {
  id: string;
  name: string;
  category: 'ingestion' | 'reasoning' | 'security' | 'execution' | 'dispatch';
  position: [number, number, number];
  color: string;
  description: string;
  telemetry: {
    latency: string;
    model: string;
    status: string;
    details: string;
  };
}

const AGENT_NODES: AgentNodeDef[] = [
  {
    id: 'ingestion',
    name: 'GitHub Issue Ingestion',
    category: 'ingestion',
    position: [-6.0, 1.5, 0],
    color: '#3B82F6',
    description: 'Ingests issue #466 from python-humanize, parses stack trace, and extracts reproduction constraints.',
    telemetry: {
      latency: '180ms',
      model: 'LangGraph Webhook Node',
      status: 'VERIFIED',
      details: 'Issue: intcomma() with negative ndigits raises unhandled ValueError.',
    },
  },
  {
    id: 'ast_parser',
    name: 'Tree-sitter AST Indexer',
    category: 'reasoning',
    position: [-4.0, 3.2, 1.2],
    color: '#8B5CF6',
    description: 'Extracts syntax trees and symbol definitions across src/humanize/ to locate vulnerable functions.',
    telemetry: {
      latency: '240ms',
      model: 'Tree-sitter Parser (Python grammar)',
      status: 'INDEXED',
      details: 'Symbol intcomma located in src/humanize/number.py (lines 50-112).',
    },
  },
  {
    id: 'context_retriever',
    name: 'AST Chunk Retrieval',
    category: 'reasoning',
    position: [-1.8, 3.8, -0.8],
    color: '#A855F7',
    description: 'Builds targeted prompt context with exact callers, docstrings, and type annotations.',
    telemetry: {
      latency: '120ms',
      model: 'Semantic Vector + AST Slicer',
      status: 'OPTIMAL',
      details: 'Context payload trimmed to 1,420 tokens; 0 extraneous lines sent to LLM.',
    },
  },
  {
    id: 'tavily_search',
    name: 'Tavily Research Node',
    category: 'reasoning',
    position: [-3.2, -1.8, -1.5],
    color: '#F59E0B',
    description: 'Queries external documentation and GitHub discussions when external API drift is detected.',
    telemetry: {
      latency: '820ms',
      model: 'Tavily Deep Search API',
      status: 'SYNCED',
      details: 'Checked PEP 3101 format specifier precision specifications.',
    },
  },
  {
    id: 'nemotron_planner',
    name: 'Nemotron 30B MoE Planner',
    category: 'reasoning',
    position: [0.0, 1.8, 0],
    color: '#76B900', // NVIDIA Emerald
    description: 'NVIDIA Nemotron 3.5 Lightning (30B A3B) executes chain-of-thought to formulate repair plan.',
    telemetry: {
      latency: '1.42s',
      model: 'nvidia/nemotron-3.5-lightning-30b-a3b (NVIDIA NIM)',
      status: 'REASONING_COMPLETE',
      details: 'Activating 3.5B params per token; produced structured JSON plan with input validation.',
    },
  },
  {
    id: 'test_synthesizer',
    name: 'Regression Test Synthesizer',
    category: 'execution',
    position: [2.2, 3.6, 1.0],
    color: '#10B981',
    description: 'Generates targeted failing pytest regression test before modifying any production code.',
    telemetry: {
      latency: '950ms',
      model: 'Nemotron 30B Synthesizer',
      status: 'SYNTHESIZED',
      details: 'Created test_intcomma_negative_ndigits() expecting ValueError.',
    },
  },
  {
    id: 'patch_validator',
    name: 'PatchValidator Security Gate',
    category: 'security',
    position: [2.0, -1.2, -1.0],
    color: '#EF4444',
    description: 'Enforces strict security checks blocking directory traversals, path injection, and credential exposure.',
    telemetry: {
      latency: '45ms',
      model: 'Deterministic AST Guard',
      status: 'APPROVED',
      details: 'Patch constrained strictly to src/humanize/number.py. Zero security violations.',
    },
  },
  {
    id: 'code_generator',
    name: 'Unified Patch Synthesizer',
    category: 'reasoning',
    position: [3.8, 1.6, 0.4],
    color: '#00E5FF',
    description: 'Produces minimal, elegant drop-in patch adding non-negative ndigits validation in intcomma().',
    telemetry: {
      latency: '1.18s',
      model: 'Nemotron 30B MoE (Temp: 0.2)',
      status: 'PATCH_READY',
      details: '+ if ndigits < 0: raise ValueError("ndigits must be non-negative")',
    },
  },
  {
    id: 'sandbox_execution',
    name: 'Isolated Sandbox Execution',
    category: 'execution',
    position: [5.8, 3.2, -0.6],
    color: '#10B981',
    description: 'Runs pytest in an isolated environment against full regression suite. 100% pass required.',
    telemetry: {
      latency: '2.10s',
      model: 'Docker Isolated Sandbox Container',
      status: '241/241 PASSED',
      details: '241 passed in 0.20s; 0 failures, 0 regressions across entire library.',
    },
  },
  {
    id: 'self_healing',
    name: 'Reflection & Self-Healing',
    category: 'execution',
    position: [4.4, -2.4, 0.8],
    color: '#F59E0B',
    description: 'Evaluates pytest stdout/stderr. If any test fails, it re-enters LangGraph reflection loop (max 3 iters).',
    telemetry: {
      latency: '35ms',
      model: 'LangGraph Conditional Router',
      status: 'NO_RETRY_NEEDED',
      details: 'First-shot success achieved. Zero test regressions detected.',
    },
  },
  {
    id: 'verification_auditor',
    name: 'Verification Gate Auditor',
    category: 'security',
    position: [6.8, -0.4, 0.6],
    color: '#76B900',
    description: 'Final multi-dimensional pass/fail check. Guarantees zero unverified code reaches production.',
    telemetry: {
      latency: '60ms',
      model: 'Deterministic Verification Gate',
      status: 'GREEN_LIGHT',
      details: 'All tests green, patch verified clean, documentation updated.',
    },
  },
  {
    id: 'pr_dispatcher',
    name: 'GitHub PR Dispatcher',
    category: 'dispatch',
    position: [8.5, 1.2, 0.0],
    color: '#3B82F6',
    description: 'Opens pull request on GitHub with comprehensive reproduction steps, test logs, and fix rationale.',
    telemetry: {
      latency: '410ms',
      model: 'GitHub REST API Client',
      status: 'PR_DISPATCHED',
      details: 'Dispatched to branch repomedic/fix/issue-466 -> PR opened.',
    },
  },
];

// Connection topology (directed LangGraph edges)
const EDGES: [string, string][] = [
  ['ingestion', 'ast_parser'],
  ['ast_parser', 'context_retriever'],
  ['ingestion', 'tavily_search'],
  ['tavily_search', 'nemotron_planner'],
  ['context_retriever', 'nemotron_planner'],
  ['nemotron_planner', 'test_synthesizer'],
  ['nemotron_planner', 'code_generator'],
  ['code_generator', 'patch_validator'],
  ['patch_validator', 'sandbox_execution'],
  ['test_synthesizer', 'sandbox_execution'],
  ['sandbox_execution', 'self_healing'],
  ['self_healing', 'verification_auditor'],
  ['verification_auditor', 'pr_dispatcher'],
];

export function ThreeAgentVisualizer() {
  const containerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [selectedNode, setSelectedNode] = useState<AgentNodeDef>(AGENT_NODES[4]); // Nemotron Planner default
  const [isAudioMuted, setIsAudioMuted] = useState(false);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(114);

  // Setup Three.js scene
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight || 520;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x06090e, 0.035);

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(0, 2, 14.5);
    camera.lookAt(0, 0.8, 0);

    // 2. WebGL Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    container.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0x76b900, 2.0); // NVIDIA green
    dirLight1.position.set(10, 20, 15);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x00e5ff, 1.8); // Cyan
    dirLight2.position.set(-10, -10, 10);
    scene.add(dirLight2);

    const pointLight = new THREE.PointLight(0xa855f7, 2.5, 30);
    pointLight.position.set(0, 3, 3);
    scene.add(pointLight);

    // 4. Background Constellation / Particle Field
    const particleCount = 750;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 45;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 35;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 35;

      const isNvidia = Math.random() > 0.6;
      colors[i * 3] = isNvidia ? 0.46 : 0.2;
      colors[i * 3 + 1] = isNvidia ? 0.72 : 0.5;
      colors[i * 3 + 2] = isNvidia ? 0.0 : 0.9;
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.12,
      vertexColors: true,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
    });
    const starField = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(starField);

    // 5. Node Meshes & Wireframe Halos
    const nodeMeshes: { [id: string]: { core: THREE.Mesh; halo: THREE.Mesh } } = {};
    const nodeLookup: { [id: string]: AgentNodeDef } = {};
    const raycastTargets: THREE.Mesh[] = [];

    AGENT_NODES.forEach((n) => {
      nodeLookup[n.id] = n;
      const group = new THREE.Group();
      group.position.set(...n.position);

      // Core sphere
      const sphereGeo = new THREE.SphereGeometry(0.55, 32, 32);
      const sphereMat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(n.color),
        roughness: 0.15,
        metalness: 0.7,
        emissive: new THREE.Color(n.color),
        emissiveIntensity: 0.45,
      });
      const core = new THREE.Mesh(sphereGeo, sphereMat);
      core.userData = { nodeId: n.id };
      group.add(core);
      raycastTargets.push(core);

      // Wireframe halo
      const haloGeo = new THREE.IcosahedronGeometry(0.85, 1);
      const haloMat = new THREE.MeshBasicMaterial({
        color: new THREE.Color(n.color),
        wireframe: true,
        transparent: true,
        opacity: 0.35,
      });
      const halo = new THREE.Mesh(haloGeo, haloMat);
      group.add(halo);

      scene.add(group);
      nodeMeshes[n.id] = { core, halo };
    });

    // 6. Directed Edges (Beziers / Curves with glowing pulse particles)
    const curveList: THREE.CatmullRomCurve3[] = [];
    EDGES.forEach(([srcId, dstId]) => {
      const src = nodeLookup[srcId];
      const dst = nodeLookup[dstId];
      if (!src || !dst) return;

      const p1 = new THREE.Vector3(...src.position);
      const p2 = new THREE.Vector3(...dst.position);
      const mid = new THREE.Vector3()
        .addVectors(p1, p2)
        .multiplyScalar(0.5)
        .add(new THREE.Vector3(0, 0.4, 0.3));

      const curve = new THREE.CatmullRomCurve3([p1, mid, p2]);
      curveList.push(curve);

      // Edge line
      const points = curve.getPoints(30);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({
        color: 0x334155,
        transparent: true,
        opacity: 0.45,
        linewidth: 1,
      });
      const line = new THREE.Line(lineGeo, lineMat);
      scene.add(line);
    });

    // 7. Animated Energy Pulses traveling along edges
    const pulseCount = 18;
    const pulseGeo = new THREE.SphereGeometry(0.12, 16, 16);
    const pulseMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.9,
    });
    const pulseMeshes: { mesh: THREE.Mesh; curveIndex: number; progress: number; speed: number }[] = [];

    for (let i = 0; i < pulseCount; i++) {
      const pMesh = new THREE.Mesh(pulseGeo, pulseMat);
      const curveIndex = i % curveList.length;
      const progress = Math.random();
      const speed = 0.003 + Math.random() * 0.004;
      scene.add(pMesh);
      pulseMeshes.push({ mesh: pMesh, curveIndex, progress, speed });
    }

    // 8. Mouse interaction (Orbit / Hover / Click)
    let isMouseDown = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let targetRotationY = 0;
    let targetRotationX = 0;

    const onMouseDown = (e: MouseEvent) => {
      isMouseDown = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      if (isMouseDown) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        targetRotationY += deltaX * 0.005;
        targetRotationX += deltaY * 0.003;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }

      // Raycast for hover
      const rect = container.getBoundingClientRect();
      const mouseX = ((e.clientX - rect.left) / container.clientWidth) * 2 - 1;
      const mouseY = -((e.clientY - rect.top) / container.clientHeight) * 2 + 1;

      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), camera);
      const intersects = raycaster.intersectObjects(raycastTargets);

      if (intersects.length > 0) {
        container.style.cursor = 'pointer';
      } else {
        container.style.cursor = isMouseDown ? 'grabbing' : 'grab';
      }
    };

    const onMouseUp = () => {
      isMouseDown = false;
    };

    const onClick = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const mouseX = ((e.clientX - rect.left) / container.clientWidth) * 2 - 1;
      const mouseY = -((e.clientY - rect.top) / container.clientHeight) * 2 + 1;

      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), camera);
      const intersects = raycaster.intersectObjects(raycastTargets);

      if (intersects.length > 0) {
        const nodeId = intersects[0].object.userData.nodeId;
        const node = nodeLookup[nodeId];
        if (node) {
          setSelectedNode(node);
          const idx = AGENT_NODES.findIndex((n) => n.id === nodeId);
          if (idx !== -1) setActiveStep(idx);
        }
      }
    };

    container.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    container.addEventListener('click', onClick);

    // 9. Resize Handler
    const onResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight || 520;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', onResize);

    // 10. Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth camera orbit damping
      camera.position.x += (Math.sin(targetRotationY) * 14.5 - camera.position.x) * 0.05;
      camera.position.z += (Math.cos(targetRotationY) * 14.5 - camera.position.z) * 0.05;
      camera.position.y += (targetRotationX * 5 + 1.8 - camera.position.y) * 0.05;
      camera.lookAt(0, 1.0, 0);

      // Subtle background rotation
      starField.rotation.y = elapsedTime * 0.02;

      // Pulse halos
      AGENT_NODES.forEach((n, idx) => {
        const meshGroup = nodeMeshes[n.id];
        if (meshGroup) {
          meshGroup.halo.rotation.x = elapsedTime * 0.5 + idx;
          meshGroup.halo.rotation.y = elapsedTime * 0.7;

          // Highlight currently active node
          const isActive = idx === activeStep;
          const targetScale = isActive ? 1.35 : 1.0;
          meshGroup.core.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
          (meshGroup.core.material as THREE.MeshStandardMaterial).emissiveIntensity = isActive
            ? 0.95 + Math.sin(elapsedTime * 6) * 0.25
            : 0.35;
        }
      });

      // Update traveling energy pulses along curves
      pulseMeshes.forEach((item) => {
        item.progress += item.speed;
        if (item.progress > 1) item.progress = 0;
        const curve = curveList[item.curveIndex];
        if (curve) {
          const pt = curve.getPoint(item.progress);
          item.mesh.position.copy(pt);
        }
      });

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      container.removeEventListener('click', onClick);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [activeStep]);

  // Step sequencer loop when playing
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setActiveStep((prev) => {
          const next = (prev + 1) % AGENT_NODES.length;
          setSelectedNode(AGENT_NODES[next]);
          return next;
        });
      }, 2400);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Audio sync controller
  const toggleAudio = () => {
    if (!audioRef.current) return;
    if (isAudioPlaying) {
      audioRef.current.pause();
      setIsAudioPlaying(false);
    } else {
      audioRef.current.play().then(() => {
        setIsAudioPlaying(true);
        setIsPlaying(true);
      }).catch((e) => {
        console.warn('Audio playback error:', e);
      });
    }
  };

  const handleAudioTimeUpdate = () => {
    if (!audioRef.current) return;
    const curr = audioRef.current.currentTime;
    setAudioCurrentTime(curr);
    
    // Map audio time (114s total) across 12 agent steps smoothly
    const stepDuration = (audioRef.current.duration || 114) / AGENT_NODES.length;
    const computedStep = Math.min(
      Math.floor(curr / stepDuration),
      AGENT_NODES.length - 1
    );
    if (computedStep !== activeStep) {
      setActiveStep(computedStep);
      setSelectedNode(AGENT_NODES[computedStep]);
    }
  };

  const formatAudioTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="rounded-2xl border border-border/80 bg-card overflow-hidden shadow-2xl relative flex flex-col">
      {/* Hidden HTML5 Audio Element playing the generated local neural narration */}
      <audio
        ref={audioRef}
        src="/assets/repomedic_pitch.mp3"
        preload="auto"
        muted={isAudioMuted}
        onTimeUpdate={handleAudioTimeUpdate}
        onLoadedMetadata={(e) => {
          setAudioDuration(e.currentTarget.duration || 114);
        }}
        onEnded={() => {
          setIsAudioPlaying(false);
          setIsPlaying(false);
        }}
      />

      {/* Top Bar Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5 bg-background/80 backdrop-blur-md border-b border-border/60 z-10">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            <span className="font-bold text-sm tracking-wide text-foreground flex items-center gap-1.5">
              Three.js Autonomous 12-Node Agent Canvas
            </span>
          </div>
          <span className="hidden sm:inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
            <Cpu className="h-3 w-3" />
            Nemotron 30B MoE Active
          </span>
        </div>

        {/* Playback Controls & Voiceover Sync */}
        <div className="flex items-center gap-2">
          {/* Audio narration sync button */}
          <button
            onClick={toggleAudio}
            className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
              isAudioPlaying
                ? 'bg-primary text-primary-foreground border-primary shadow-sm ring-2 ring-primary/30'
                : 'bg-muted/70 hover:bg-muted text-foreground border-border'
            }`}
            title="Play high-fidelity local neural narration synced to 3D pipeline"
          >
            {isAudioPlaying ? (
              <>
                <Volume2 className="h-3.5 w-3.5 animate-pulse text-emerald-400" />
                <span>Narration Playing ({formatAudioTime(audioCurrentTime)})</span>
              </>
            ) : (
              <>
                <Volume2 className="h-3.5 w-3.5" />
                <span>Play Voiceover (100% Local TTS)</span>
              </>
            )}
          </button>

          {/* Mute button */}
          <button
            onClick={() => setIsAudioMuted(!isAudioMuted)}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border"
            title={isAudioMuted ? 'Unmute' : 'Mute'}
          >
            {isAudioMuted ? <VolumeX className="h-3.5 w-3.5" /> : <Volume2 className="h-3.5 w-3.5" />}
          </button>

          {/* Play/Pause state machine stepper */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="p-1.5 rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
            title={isPlaying ? 'Pause Simulation' : 'Play Autonomous Pipeline'}
          >
            {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
          </button>

          {/* Reset button */}
          <button
            onClick={() => {
              setActiveStep(0);
              setSelectedNode(AGENT_NODES[0]);
              if (audioRef.current) audioRef.current.currentTime = 0;
            }}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors border border-border"
            title="Reset Simulation"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {/* Main 3D Canvas Container */}
      <div className="relative w-full h-[520px] bg-[#06090e] select-none">
        <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

        {/* Orbit instruction badge */}
        <div className="absolute top-4 left-4 pointer-events-none hidden sm:flex items-center gap-1.5 text-[11px] text-muted-foreground bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-md border border-white/10 font-mono">
          <Info className="h-3 w-3 text-emerald-400" />
          Click & Drag to Orbit 3D Graph • Click Nodes to Inspect
        </div>

        {/* Current Active Step Badge in 3D overlay */}
        <div className="absolute top-4 right-4 bg-black/70 backdrop-blur-md border border-white/10 rounded-xl p-3 max-w-xs shadow-xl hidden md:block">
          <div className="text-[10px] font-mono uppercase text-emerald-400 font-semibold tracking-wider flex items-center gap-1">
            <Sparkles className="h-3 w-3" /> Step {activeStep + 1} of 12
          </div>
          <p className="text-sm font-bold text-white mt-0.5 truncate">
            {AGENT_NODES[activeStep].name}
          </p>
          <p className="text-xs text-zinc-400 mt-1 line-clamp-2">
            {AGENT_NODES[activeStep].description}
          </p>
        </div>

        {/* Selected Node Telemetry Inspector Panel (Floating at bottom of canvas) */}
        <div className="absolute bottom-4 left-4 right-4 bg-black/85 backdrop-blur-lg border border-white/10 rounded-xl p-4 shadow-2xl transition-all">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-white/10">
            <div className="flex items-center gap-2.5">
              <span 
                className="w-3.5 h-3.5 rounded-full shrink-0 shadow-sm" 
                style={{ backgroundColor: selectedNode.color }} 
              />
              <div>
                <h4 className="font-bold text-sm text-white flex items-center gap-2">
                  {selectedNode.name}
                  <span className="text-[10px] px-2 py-0.5 rounded font-mono uppercase bg-white/10 text-zinc-300">
                    {selectedNode.category}
                  </span>
                </h4>
                <p className="text-xs text-zinc-400 mt-0.5">{selectedNode.description}</p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono shrink-0">
              <div>
                <span className="text-zinc-500 block text-[10px]">LATENCY</span>
                <span className="text-emerald-400 font-bold">{selectedNode.telemetry.latency}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px]">STATUS</span>
                <span className="text-cyan-400 font-bold">{selectedNode.telemetry.status}</span>
              </div>
            </div>
          </div>

          <div className="pt-2.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div className="font-mono text-zinc-300 flex items-center gap-2 truncate">
              <Terminal className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
              <span className="text-zinc-400">ENGINE:</span>
              <span className="text-white truncate">{selectedNode.telemetry.model}</span>
            </div>
            <div className="font-mono text-zinc-300 flex items-center gap-2 truncate">
              <span className="text-zinc-500">PAYLOAD:</span>
              <span className="text-zinc-300 truncate">{selectedNode.telemetry.details}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Sequencer Node Step Progress Bar */}
      <div className="bg-background/90 px-4 py-3 border-t border-border/80 flex items-center gap-1.5 overflow-x-auto scrollbar-none">
        {AGENT_NODES.map((node, i) => {
          const isActive = i === activeStep;
          const isPassed = i < activeStep;
          return (
            <button
              key={node.id}
              onClick={() => {
                setActiveStep(i);
                setSelectedNode(node);
                if (audioRef.current && audioDuration > 0) {
                  audioRef.current.currentTime = (i / AGENT_NODES.length) * audioDuration;
                }
              }}
              className={`flex-1 min-w-[70px] py-1.5 px-2 rounded-lg text-left transition-all border ${
                isActive
                  ? 'bg-primary/10 border-primary text-primary font-semibold'
                  : isPassed
                  ? 'bg-muted/40 border-emerald-500/30 text-emerald-400'
                  : 'bg-muted/10 border-border/40 text-muted-foreground hover:bg-muted/30'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono">0{i + 1}</span>
                {isPassed ? (
                  <CheckCircle2 className="h-2.5 w-2.5 text-emerald-400" />
                ) : (
                  <span 
                    className="w-1.5 h-1.5 rounded-full" 
                    style={{ backgroundColor: node.color }} 
                  />
                )}
              </div>
              <p className="text-[11px] truncate mt-0.5 leading-tight">{node.name.split(' ')[0]}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
