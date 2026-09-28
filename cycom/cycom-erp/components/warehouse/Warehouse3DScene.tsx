'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { useT } from '@/lib/i18n';
import { DEFAULT_SIZE, FlatLocationNode, TYPE_HEIGHT, occupancyHexColor } from '@/lib/warehouseHeat';

const UNIT = 1; // one floor-plan unit == one three.js world unit

interface Warehouse3DSceneProps {
  nodes: FlatLocationNode[];
}

interface SelectedInfo {
  code: string;
  parentPath: string;
  occupancy: number | null;
  qty: number;
}

/**
 * Real 3D warehouse render (Three.js): each placed location becomes an
 * extruded box positioned by its 2D floor-plan coordinates, colored by the
 * same occupancy heat scale as the 2D map and the list view. Deliberately
 * plain `three` + OrbitControls rather than a React-Three-Fiber scene graph
 * -- one static-ish scene that just needs to re-diff boxes when `nodes`
 * changes, not a full declarative render tree.
 */
export default function Warehouse3DScene({ nodes }: Warehouse3DSceneProps) {
  const t = useT();
  const mountRef = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState<SelectedInfo | null>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const width = mount.clientWidth;
    const height = mount.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0a0f1e');

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 500);
    camera.position.set(18, 16, 18);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(8, 0, 8);
    controls.update();

    scene.add(new THREE.AmbientLight(0xffffff, 0.6));
    const dir = new THREE.DirectionalLight(0xffffff, 0.8);
    dir.position.set(20, 30, 10);
    scene.add(dir);

    const grid = new THREE.GridHelper(60, 60, 0x334155, 0x1e293b);
    scene.add(grid);

    const meshes: { mesh: THREE.Mesh; node: FlatLocationNode }[] = [];
    nodes
      .filter((n) => n.pos_x !== null && n.pos_y !== null)
      .forEach((n) => {
        const def = DEFAULT_SIZE[n.location_type] || { w: 1, d: 1 };
        const w = (n.size_w ?? def.w) * UNIT;
        const d = (n.size_d ?? def.d) * UNIT;
        const h = TYPE_HEIGHT[n.location_type] ?? 1;
        const geometry = new THREE.BoxGeometry(w, h, d);
        const color = new THREE.Color(occupancyHexColor(n.occupancy_percent));
        const material = new THREE.MeshStandardMaterial({ color, transparent: true, opacity: 0.85 });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set((n.pos_x ?? 0) * UNIT + w / 2, h / 2, (n.pos_y ?? 0) * UNIT + d / 2);
        scene.add(mesh);

        const edges = new THREE.LineSegments(
          new THREE.EdgesGeometry(geometry),
          new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.25 }),
        );
        edges.position.copy(mesh.position);
        scene.add(edges);

        meshes.push({ mesh, node: n });
      });

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();

    const handleClick = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hit = raycaster.intersectObjects(meshes.map((m) => m.mesh))[0];
      if (hit) {
        const found = meshes.find((m) => m.mesh === hit.object);
        if (found) {
          setSelected({
            code: found.node.code,
            parentPath: found.node.parent_path,
            occupancy: found.node.occupancy_percent,
            qty: found.node.total_quantity,
          });
        }
      } else {
        setSelected(null);
      }
    };
    renderer.domElement.addEventListener('click', handleClick);

    let frameId: number;
    const animate = () => {
      frameId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const resizeObserver = new ResizeObserver(() => {
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
    resizeObserver.observe(mount);

    return () => {
      cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener('click', handleClick);
      controls.dispose();
      meshes.forEach(({ mesh }) => {
        mesh.geometry.dispose();
        (mesh.material as THREE.Material).dispose();
      });
      renderer.dispose();
      if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement);
    };
  }, [nodes]);

  const anyPlaced = nodes.some((n) => n.pos_x !== null);

  return (
    <div className="relative rounded-xl border border-slate-850 overflow-hidden" style={{ height: 460 }}>
      <div ref={mountRef} className="w-full h-full" />
      {!anyPlaced && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-600 text-xs bg-[#0a0f1e]">
          {t('warehouseMap.noPlacements')}
        </div>
      )}
      {selected && (
        <div className="absolute top-3 start-3 p-3 rounded-xl bg-slate-950/90 border border-slate-800 backdrop-blur text-[11px] space-y-1 min-w-[160px]">
          <p className="font-bold text-white">{selected.code}</p>
          {selected.parentPath && <p className="text-slate-500 text-[10px]">{selected.parentPath}</p>}
          <p className="text-slate-400">{t('warehouseMap.totalQty')}: <span className="font-mono text-slate-200">{selected.qty.toLocaleString()}</span></p>
          {selected.occupancy !== null && (
            <p className="text-slate-400">{t('warehouseMap.occupancyLabel')}: <span className="font-mono text-slate-200">{selected.occupancy}%</span></p>
          )}
        </div>
      )}
    </div>
  );
}
