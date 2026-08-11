import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { CadHole } from '../../api/cadApi';

interface CadViewer3DProps {
  meshData?: {
    vertices: number[][];
    faces: number[][];
    normals: number[][];
  };
  holes?: CadHole[];
  selectedHoleId?: number | null;
  onSelectHole?: (hole: CadHole) => void;
}

export const CadViewer3D: React.FC<CadViewer3DProps> = ({
  meshData,
  holes = [],
  selectedHoleId,
  onSelectHole,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth || 600;
    const height = mountRef.current.clientHeight || 400;

    // Three.js Scene, Camera, Renderer
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0f172a');

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(100, 80, 120);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    mountRef.current.appendChild(renderer.domElement);

    // Lightings
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
    dirLight.position.set(100, 200, 150);
    scene.add(dirLight);

    const backLight = new THREE.DirectionalLight(0x818cf8, 0.5);
    backLight.position.set(-100, -100, -100);
    scene.add(backLight);

    // Grid helper
    const grid = new THREE.GridHelper(200, 20, 0x3b82f6, 0x1e293b);
    grid.position.y = -15;
    scene.add(grid);

    // Build 3D CAD Mesh
    if (meshData && meshData.vertices.length > 0) {
      const geometry = new THREE.BufferGeometry();

      const positions: number[] = [];
      meshData.faces.forEach((face) => {
        const v0 = meshData.vertices[face[0]];
        const v1 = meshData.vertices[face[1]];
        const v2 = meshData.vertices[face[2]];
        positions.push(...v0, ...v1, ...v2);
      });

      geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
      geometry.computeVertexNormals();

      const material = new THREE.MeshStandardMaterial({
        color: 0x475569,
        metalness: 0.3,
        roughness: 0.4,
        wireframe: false,
      });

      const cadMesh = new THREE.Mesh(geometry, material);
      scene.add(cadMesh);

      // Wireframe overlay
      const wireframeMat = new THREE.MeshBasicMaterial({ color: 0x94a3b8, wireframe: true, transparent: true, opacity: 0.15 });
      const wireframeMesh = new THREE.Mesh(geometry, wireframeMat);
      scene.add(wireframeMesh);
    } else {
      // Demo 3B Lug Part (Fallback Visual)
      const boxGeo = new THREE.BoxGeometry(100, 50, 6);
      const boxMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.4, roughness: 0.3 });
      const demoMesh = new THREE.Mesh(boxGeo, boxMat);
      scene.add(demoMesh);
    }

    // Render Detected Hole Pins / Markers
    holes.forEach((hole) => {
      const isSelected = hole.id === selectedHoleId;
      const markerColor = isSelected ? 0xef4444 : 0x10b981;

      // Hole Pin Cylinder
      const cylGeo = new THREE.CylinderGeometry(hole.diameter / 2, hole.diameter / 2, 20, 16);
      const cylMat = new THREE.MeshStandardMaterial({
        color: markerColor,
        metalness: 0.8,
        roughness: 0.2,
        transparent: true,
        opacity: 0.85,
      });
      const pin = new THREE.Mesh(cylGeo, cylMat);
      pin.position.set(hole.center[0] - 50, hole.center[1] - 25, hole.center[2]);
      pin.userData = { hole };
      scene.add(pin);
    });

    // Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      scene.rotation.y += 0.002;
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [meshData, holes, selectedHoleId]);

  return (
    <div className="relative w-full h-[450px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 shadow-2xl">
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
      <div className="absolute top-4 left-4 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-sky-400 font-mono flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
        Three.js 3B CAD WebGL Engine Active
      </div>
      <div className="absolute bottom-4 right-4 bg-slate-900/80 backdrop-blur-md px-3 py-1 text-[11px] text-slate-400 rounded border border-slate-800">
        🖱️ Sol tık: Döndür | Scroll: Zoom
      </div>
    </div>
  );
};
