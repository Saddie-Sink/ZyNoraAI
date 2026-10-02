import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';

export const RENDER_STYLES = {
  photorealistic: {
    label: 'Photorealistic',
    desc: 'Warm oak hardwood, Carrara marble & contemporary 3D furniture',
    wallColor: 0xffffff,
    wallCapColor: 0x1e293b,
    slabColor: 0xf8fafc,
    edgeColor: null,
  },
  minimalist: {
    label: 'Minimalist',
    desc: 'Scandinavian birch, matte plaster & neutral linen palette',
    wallColor: 0xfafaf9,
    wallCapColor: 0x475569,
    slabColor: 0xf5f5f4,
    edgeColor: null,
  },
  blueprint: {
    label: 'Blueprint',
    desc: 'Architectural cobalt CAD 3D projection with glowing cyan edges',
    wallColor: 0x1e3a8a,
    wallCapColor: 0x38bdf8,
    slabColor: 0x0f2942,
    edgeColor: 0x38bdf8,
  },
  sketch: {
    label: 'Sketch',
    desc: 'Architectural ink & marker axonometric illustration',
    wallColor: 0xfaf8f5,
    wallCapColor: 0x0f172a,
    slabColor: 0xf5f0eb,
    edgeColor: 0x334155,
  },
};

export const VIEW_ANGLES = {
  birds_eye: {
    label: "Bird's Eye",
    desc: 'High-angle 65° top-down isometric view',
    theta: Math.PI * 0.18,
    phi: Math.PI * 0.18,
    radiusMult: 1.25,
  },
  angled: {
    label: 'Angled 3D',
    desc: 'Classic 45° architectural dollhouse cutaway',
    theta: Math.PI * 0.24,
    phi: Math.PI * 0.32,
    radiusMult: 1.35,
  },
  room_focused: {
    label: 'Close-Up',
    desc: '35° interior close-up perspective',
    theta: Math.PI * 0.16,
    phi: Math.PI * 0.38,
    radiusMult: 0.95,
  },
  exterior: {
    label: 'Exterior 3D',
    desc: 'Oblique full villa perspective',
    theta: Math.PI * 0.28,
    phi: Math.PI * 0.38,
    radiusMult: 1.55,
  },
};

export const BG_MODES = {
  white: {
    label: 'Pure White',
    bg: '#FFFFFF',
    threeBg: 0xffffff,
  },
  studio: {
    label: 'Soft Studio',
    bg: '#F8FAFC',
    threeBg: 0xf8fafc,
  },
  dark: {
    label: 'Dark Slate',
    bg: '#0F172A',
    threeBg: 0x0f172a,
  },
};

// ─── Procedural PBR Floor Texture Generators ────────────────────────────────
function createWoodPlankTexture(roomType, styleKey) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');

  if (styleKey === 'blueprint') {
    ctx.fillStyle = '#122B4A';
    ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.25)';
    ctx.lineWidth = 2;
    for (let i = 0; i <= 512; i += 64) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
    }
  } else if (styleKey === 'minimalist') {
    // Pale Birch Scandinavian Wood
    ctx.fillStyle = '#F5EBE1';
    ctx.fillRect(0, 0, 512, 512);
    const tones = ['#F7EFE7', '#F2E5D8', '#EFE0D0', '#F9F2EB'];
    for (let row = 0; row < 8; row++) {
      const y = row * 64;
      const offset = (row % 2) * 128;
      for (let col = -1; col < 4; col++) {
        const x = col * 256 + offset;
        ctx.fillStyle = tones[(row * 2 + col + 4) % tones.length];
        ctx.fillRect(x, y, 256, 64);
        ctx.strokeStyle = 'rgba(168, 140, 116, 0.25)';
        ctx.lineWidth = 1.5;
        ctx.strokeRect(x, y, 256, 64);
      }
    }
  } else {
    // Warm European Oak Hardwood Planks (floor-plan.ai look)
    const baseColor = roomType === 'bedroom' ? '#D4A36E' : '#DFB584';
    ctx.fillStyle = baseColor;
    ctx.fillRect(0, 0, 512, 512);
    const tones = ['#D4A36E', '#DFB584', '#C99660', '#E4BE91', '#CFA06A'];
    for (let row = 0; row < 8; row++) {
      const y = row * 64;
      const offset = (row % 2) * 128;
      for (let col = -1; col < 4; col++) {
        const x = col * 256 + offset;
        ctx.fillStyle = tones[(row * 3 + col + 5) % tones.length];
        ctx.fillRect(x, y, 256, 64);

        // Fine grain lines
        ctx.strokeStyle = 'rgba(120, 53, 15, 0.08)';
        ctx.lineWidth = 1.5;
        for (let g = 10; g < 64; g += 14) {
          ctx.beginPath();
          ctx.moveTo(x, y + g);
          ctx.lineTo(x + 256, y + g + (col % 2 === 0 ? 1 : -1));
          ctx.stroke();
        }

        // Seam bevel
        ctx.strokeStyle = 'rgba(92, 45, 12, 0.32)';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, 256, 64);
      }
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function createMarbleTileTexture(styleKey) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');

  if (styleKey === 'blueprint') {
    ctx.fillStyle = '#0F2942';
    ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 2.5;
    for (let i = 0; i <= 512; i += 128) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
    }
  } else {
    // Polished Carrara Marble with subtle grey veining
    ctx.fillStyle = '#F8FAFC';
    ctx.fillRect(0, 0, 512, 512);

    ctx.strokeStyle = 'rgba(148, 163, 184, 0.22)';
    ctx.lineWidth = 2.5;
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.moveTo(i * 110, 0);
      ctx.bezierCurveTo(i * 110 + 40, 160, i * 110 - 30, 360, i * 110 + 60, 512);
      ctx.stroke();
    }

    // Grout lines
    ctx.strokeStyle = '#CBD5E1';
    ctx.lineWidth = 3;
    for (let i = 0; i <= 512; i += 128) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function createCeramicMosaicTexture(styleKey) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');

  if (styleKey === 'blueprint') {
    ctx.fillStyle = '#172554';
    ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 1.5;
    for (let i = 0; i <= 512; i += 64) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
    }
  } else {
    // Aqua-white mosaic grid for bathrooms
    ctx.fillStyle = '#E0F2FE';
    ctx.fillRect(0, 0, 512, 512);
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        ctx.fillStyle = (r + c) % 2 === 0 ? '#E0F2FE' : '#BAE6FD';
        ctx.fillRect(c * 64, r * 64, 64, 64);
      }
    }
    ctx.strokeStyle = '#94A3B8';
    ctx.lineWidth = 2.5;
    for (let i = 0; i <= 512; i += 64) {
      ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, 512); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(512, i); ctx.stroke();
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

function createBalconyDeckTexture(styleKey) {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d');

  if (styleKey === 'blueprint') {
    ctx.fillStyle = '#0F2942';
    ctx.fillRect(0, 0, 512, 512);
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 2;
    for (let y = 0; y <= 512; y += 32) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(512, y); ctx.stroke();
    }
  } else {
    ctx.fillStyle = '#D97706';
    ctx.fillRect(0, 0, 512, 512);
    for (let y = 0; y < 512; y += 32) {
      ctx.fillStyle = (y / 32) % 2 === 0 ? '#C27838' : '#B56B2B';
      ctx.fillRect(0, y, 512, 28);
      ctx.fillStyle = '#78350F';
      ctx.fillRect(0, y + 28, 512, 4);
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  return texture;
}

// ─── 3D Architectural Furniture Synthesizer ──────────────────────────────────
function buildRoomFurnitureGroup(room, styleKey) {
  const group = new THREE.Group();
  const type = (room.type || room.name || '').toLowerCase();
  const rw = Number(room.width) || 10;
  const rd = Number(room.height || room.depth) || 10;
  const cx = 0;
  const cz = 0;

  const woodColor = styleKey === 'blueprint' ? 0x2563eb : 0xd4a36e;
  const fabricColor = styleKey === 'blueprint' ? 0x1e40af : 0xf1f5f9;
  const accentColor = styleKey === 'blueprint' ? 0x38bdf8 : 0xd97706;
  const darkMetal = styleKey === 'blueprint' ? 0x38bdf8 : 0x1e293b;

  // 1. BEDROOM FURNITURE (Queen/King bed with headboard, pillows, duvet, nightstands)
  if (type.includes('bed') && rw >= 7 && rd >= 7) {
    const bedW = Math.min(rw * 0.48, 6.2);
    const bedD = Math.min(rd * 0.52, 6.8);
    const bedH = 1.15;

    // Bed frame
    const frameGeo = new THREE.BoxGeometry(bedW, 0.45, bedD);
    const frameMat = new THREE.MeshStandardMaterial({ color: woodColor, roughness: 0.5 });
    const frameMesh = new THREE.Mesh(frameGeo, frameMat);
    frameMesh.position.set(cx, 0.22, cz);
    frameMesh.castShadow = true;
    frameMesh.receiveShadow = true;
    group.add(frameMesh);

    // Mattress & White Duvet
    const matGeo = new THREE.BoxGeometry(bedW - 0.2, 0.55, bedD - 0.2);
    const matMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.8 });
    const matMesh = new THREE.Mesh(matGeo, matMat);
    matMesh.position.set(cx, 0.65, cz);
    matMesh.castShadow = true;
    group.add(matMesh);

    // Headboard
    const hbGeo = new THREE.BoxGeometry(bedW, 1.85, 0.35);
    const hbMat = new THREE.MeshStandardMaterial({ color: woodColor, roughness: 0.4 });
    const hbMesh = new THREE.Mesh(hbGeo, hbMat);
    hbMesh.position.set(cx, 0.92, cz - bedD / 2 + 0.18);
    hbMesh.castShadow = true;
    group.add(hbMesh);

    // Pillows
    const pilW = bedW * 0.36;
    const pilD = 1.1;
    const pilGeo = new THREE.BoxGeometry(pilW, 0.25, pilD);
    const pilMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9 });
    const pil1 = new THREE.Mesh(pilGeo, pilMat);
    pil1.position.set(cx - bedW * 0.24, 1.0, cz - bedD / 2 + 0.9);
    const pil2 = new THREE.Mesh(pilGeo, pilMat);
    pil2.position.set(cx + bedW * 0.24, 1.0, cz - bedD / 2 + 0.9);
    group.add(pil1, pil2);

    // Dual Nightstands
    const nsGeo = new THREE.BoxGeometry(1.2, 0.85, 1.2);
    const nsMat = new THREE.MeshStandardMaterial({ color: woodColor, roughness: 0.5 });
    const ns1 = new THREE.Mesh(nsGeo, nsMat);
    ns1.position.set(cx - bedW / 2 - 0.85, 0.42, cz - bedD / 2 + 0.6);
    ns1.castShadow = true;
    const ns2 = new THREE.Mesh(nsGeo, nsMat);
    ns2.position.set(cx + bedW / 2 + 0.85, 0.42, cz - bedD / 2 + 0.6);
    ns2.castShadow = true;
    group.add(ns1, ns2);

    // Wardrobe along opposite wall
    if (rw >= 9) {
      const wardW = Math.min(rw * 0.42, 5.5);
      const wardGeo = new THREE.BoxGeometry(wardW, 3.6, 1.4);
      const wardMat = new THREE.MeshStandardMaterial({ color: woodColor, roughness: 0.4 });
      const wardMesh = new THREE.Mesh(wardGeo, wardMat);
      wardMesh.position.set(cx - rw / 2 + wardW / 2 + 0.6, 1.8, cz + rd / 2 - 0.9);
      wardMesh.castShadow = true;
      group.add(wardMesh);
    }
  }

  // 2. LIVING ROOM FURNITURE (Sectional sofa, coffee table, media console, rug)
  else if (type.includes('living') && rw >= 8 && rd >= 8) {
    const sofaW = Math.min(rw * 0.54, 7.5);
    const sofaD = Math.min(rd * 0.35, 4.5);

    // Area Rug
    const rugGeo = new THREE.BoxGeometry(sofaW * 1.2, 0.04, sofaD * 1.2);
    const rugMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, roughness: 0.9 });
    const rugMesh = new THREE.Mesh(rugGeo, rugMat);
    rugMesh.position.set(cx, 0.02, cz);
    rugMesh.receiveShadow = true;
    group.add(rugMesh);

    // Main Sofa Section
    const sofaGeo = new THREE.BoxGeometry(sofaW, 1.2, 2.2);
    const sofaMat = new THREE.MeshStandardMaterial({ color: fabricColor, roughness: 0.7 });
    const sofaMesh = new THREE.Mesh(sofaGeo, sofaMat);
    sofaMesh.position.set(cx, 0.6, cz + sofaD / 2 - 1.1);
    sofaMesh.castShadow = true;
    group.add(sofaMesh);

    // Sofa Backrest
    const backGeo = new THREE.BoxGeometry(sofaW, 0.8, 0.55);
    const backMat = new THREE.MeshStandardMaterial({ color: fabricColor, roughness: 0.7 });
    const backMesh = new THREE.Mesh(backGeo, backMat);
    backMesh.position.set(cx, 1.4, cz + sofaD / 2 - 0.35);
    group.add(backMesh);

    // L-Section
    const lGeo = new THREE.BoxGeometry(2.0, 1.2, 2.4);
    const lMesh = new THREE.Mesh(lGeo, sofaMat);
    lMesh.position.set(cx - sofaW / 2 + 1.0, 0.6, cz - 0.6);
    lMesh.castShadow = true;
    group.add(lMesh);

    // Coffee Table
    const ctGeo = new THREE.BoxGeometry(sofaW * 0.44, 0.65, 1.6);
    const ctMat = new THREE.MeshStandardMaterial({ color: woodColor, roughness: 0.4 });
    const ctMesh = new THREE.Mesh(ctGeo, ctMat);
    ctMesh.position.set(cx + 0.4, 0.32, cz - 0.5);
    ctMesh.castShadow = true;
    group.add(ctMesh);

    // TV Media Console
    const tvGeo = new THREE.BoxGeometry(sofaW * 0.65, 0.95, 0.9);
    const tvMat = new THREE.MeshStandardMaterial({ color: darkMetal, roughness: 0.3 });
    const tvMesh = new THREE.Mesh(tvGeo, tvMat);
    tvMesh.position.set(cx, 0.48, cz - rd / 2 + 0.8);
    tvMesh.castShadow = true;
    group.add(tvMesh);
  }

  // 3. DINING ROOM FURNITURE (Wooden table + 6 chairs)
  else if (type.includes('dining') && rw >= 6.5 && rd >= 6.5) {
    const tableW = Math.min(rw * 0.46, 5.2);
    const tableD = Math.min(rd * 0.38, 3.2);

    // Table Top
    const tableGeo = new THREE.BoxGeometry(tableW, 0.22, tableD);
    const tableMat = new THREE.MeshStandardMaterial({ color: woodColor, roughness: 0.3 });
    const tableMesh = new THREE.Mesh(tableGeo, tableMat);
    tableMesh.position.set(cx, 1.35, cz);
    tableMesh.castShadow = true;
    group.add(tableMesh);

    // 4 Table Legs
    const legGeo = new THREE.BoxGeometry(0.24, 1.35, 0.24);
    const legMat = new THREE.MeshStandardMaterial({ color: darkMetal, roughness: 0.4 });
    [
      [-tableW / 2 + 0.3, -tableD / 2 + 0.3],
      [tableW / 2 - 0.3, -tableD / 2 + 0.3],
      [-tableW / 2 + 0.3, tableD / 2 - 0.3],
      [tableW / 2 - 0.3, tableD / 2 - 0.3],
    ].forEach(([lx, lz]) => {
      const leg = new THREE.Mesh(legGeo, legMat);
      leg.position.set(cx + lx, 0.68, cz + lz);
      leg.castShadow = true;
      group.add(leg);
    });

    // Chairs
    const chairGeo = new THREE.BoxGeometry(0.95, 0.16, 0.95);
    const chairBackGeo = new THREE.BoxGeometry(0.95, 1.0, 0.16);
    const chairMat = new THREE.MeshStandardMaterial({ color: fabricColor, roughness: 0.8 });
    [-tableW * 0.28, tableW * 0.28].forEach((chairX) => {
      // North Chair
      const cN = new THREE.Mesh(chairGeo, chairMat);
      cN.position.set(cx + chairX, 0.85, cz - tableD / 2 - 0.6);
      const cbN = new THREE.Mesh(chairBackGeo, chairMat);
      cbN.position.set(cx + chairX, 1.35, cz - tableD / 2 - 1.0);
      // South Chair
      const cS = new THREE.Mesh(chairGeo, chairMat);
      cS.position.set(cx + chairX, 0.85, cz + tableD / 2 + 0.6);
      const cbS = new THREE.Mesh(chairBackGeo, chairMat);
      cbS.position.set(cx + chairX, 1.35, cz + tableD / 2 + 1.0);
      group.add(cN, cbN, cS, cbS);
    });
  }

  // 4. KITCHEN FURNITURE (L-counter with cooktop hob, sink, and cabinets)
  else if (type.includes('kitchen') && rw >= 5.5 && rd >= 5.5) {
    const counterD = 1.8;
    const topW = rw - 0.8;

    // Main Counter
    const mcGeo = new THREE.BoxGeometry(topW, 1.45, counterD);
    const mcMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2 });
    const mcMesh = new THREE.Mesh(mcGeo, mcMat);
    mcMesh.position.set(cx, 0.72, cz - rd / 2 + counterD / 2 + 0.4);
    mcMesh.castShadow = true;
    group.add(mcMesh);

    // Black Ceramic Cooktop Hob
    const hobGeo = new THREE.BoxGeometry(1.9, 0.08, 1.2);
    const hobMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.1 });
    const hobMesh = new THREE.Mesh(hobGeo, hobMat);
    hobMesh.position.set(cx + topW * 0.2, 1.48, cz - rd / 2 + counterD / 2 + 0.4);
    group.add(hobMesh);

    // Chrome Undermount Sink
    const sinkGeo = new THREE.BoxGeometry(1.6, 0.08, 1.1);
    const sinkMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8, roughness: 0.2 });
    const sinkMesh = new THREE.Mesh(sinkGeo, sinkMat);
    sinkMesh.position.set(cx - topW * 0.2, 1.48, cz - rd / 2 + counterD / 2 + 0.4);
    group.add(sinkMesh);

    // Side L-Counter if room is wide enough
    if (rd >= 7) {
      const sideH = rd * 0.42;
      const scGeo = new THREE.BoxGeometry(counterD, 1.45, sideH);
      const scMesh = new THREE.Mesh(scGeo, mcMat);
      scMesh.position.set(cx + rw / 2 - counterD / 2 - 0.4, 0.72, cz - rd / 2 + counterD + sideH / 2 + 0.2);
      scMesh.castShadow = true;
      group.add(scMesh);
    }
  }

  // 5. BATHROOM FIXTURES (Ceramic WC toilet, vanity basin, glass shower)
  else if (type.includes('bath') || type.includes('wc') || type.includes('toilet')) {
    // WC Toilet Tank & Bowl
    const cisternGeo = new THREE.BoxGeometry(1.2, 1.4, 0.6);
    const whiteCeramic = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.15 });
    const cisternMesh = new THREE.Mesh(cisternGeo, whiteCeramic);
    cisternMesh.position.set(cx - rw / 2 + 1.0, 0.8, cz - rd / 2 + 0.6);
    cisternMesh.castShadow = true;

    const bowlGeo = new THREE.CylinderGeometry(0.55, 0.45, 0.8, 16);
    const bowlMesh = new THREE.Mesh(bowlGeo, whiteCeramic);
    bowlMesh.position.set(cx - rw / 2 + 1.0, 0.4, cz - rd / 2 + 1.3);
    group.add(cisternMesh, bowlMesh);

    // Vanity Sink Counter
    const vanW = Math.min(rw * 0.38, 2.4);
    const vanGeo = new THREE.BoxGeometry(vanW, 1.3, 1.3);
    const vanMesh = new THREE.Mesh(vanGeo, whiteCeramic);
    vanMesh.position.set(cx + rw / 2 - vanW / 2 - 0.6, 0.65, cz - rd / 2 + 1.0);
    vanMesh.castShadow = true;
    group.add(vanMesh);

    // Glass Shower Screen
    const glassGeo = new THREE.BoxGeometry(0.12, 3.2, Math.min(rd * 0.45, 3.2));
    const glassMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.45,
      roughness: 0.1,
    });
    const glassMesh = new THREE.Mesh(glassGeo, glassMat);
    glassMesh.position.set(cx + rw / 2 - 2.8, 1.6, cz + rd / 2 - 1.8);
    group.add(glassMesh);
  }

  // 6. POOJA MANDIR (Warm wooden altar shrine with brass accents)
  else if (type.includes('pooja') || type.includes('mandir')) {
    const mandirGeo = new THREE.BoxGeometry(Math.min(rw * 0.5, 3.2), 2.4, 1.5);
    const mandirMat = new THREE.MeshStandardMaterial({ color: woodColor, roughness: 0.4 });
    const mandirMesh = new THREE.Mesh(mandirGeo, mandirMat);
    mandirMesh.position.set(cx, 1.2, cz - rd / 2 + 1.0);
    mandirMesh.castShadow = true;
    group.add(mandirMesh);
  }

  // 7. BALCONY / TERRACE (Slatted glass railing & outdoor lounge)
  else if (type.includes('balcony') || type.includes('verandah') || type.includes('deck')) {
    const railGeo = new THREE.BoxGeometry(rw - 0.4, 1.6, 0.15);
    const railMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.5 });
    const railMesh = new THREE.Mesh(railGeo, railMat);
    railMesh.position.set(cx, 0.8, cz - rd / 2 + 0.3);
    group.add(railMesh);
  }

  return group;
}

export default function Interactive3DViewer({
  candidate,
  activeFloorIdx = 0,
  externalRenderStyle = 'photorealistic',
  externalViewAngle = 'birds_eye',
  externalBgMode = 'white',
  height = 560,
}) {
  const mountRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const sceneRef = useRef(null);
  const animIdRef = useRef(null);

  const [renderStyle, setRenderStyle] = useState(externalRenderStyle || 'photorealistic');
  const [viewAngle, setViewAngle] = useState(externalViewAngle || 'birds_eye');
  const [bgMode, setBgMode] = useState(externalBgMode || 'white');
  const [autoRotate, setAutoRotate] = useState(false);

  const camSphericalRef = useRef({
    radius: 46,
    theta: Math.PI * 0.18,
    phi: Math.PI * 0.22,
    targetX: 0,
    targetY: 1.8,
    targetZ: 0,
  });

  useEffect(() => {
    if (externalRenderStyle && RENDER_STYLES[externalRenderStyle]) {
      setRenderStyle(externalRenderStyle);
    }
  }, [externalRenderStyle]);

  useEffect(() => {
    if (externalViewAngle && VIEW_ANGLES[externalViewAngle]) {
      setViewAngle(externalViewAngle);
      const preset = VIEW_ANGLES[externalViewAngle];
      camSphericalRef.current.theta = preset.theta;
      camSphericalRef.current.phi = preset.phi;
    }
  }, [externalViewAngle]);

  useEffect(() => {
    if (externalBgMode && BG_MODES[externalBgMode]) {
      setBgMode(externalBgMode);
    }
  }, [externalBgMode]);

  // Main Three.js Scene Setup & Geometry Construction
  useEffect(() => {
    const dom = mountRef.current;
    if (!dom || !candidate) return;

    const width = dom.clientWidth || 800;
    const canvasHeight = height || 560;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    const bgInfo = BG_MODES[bgMode] || BG_MODES.white;
    scene.background = new THREE.Color(bgInfo.threeBg);

    const camera = new THREE.PerspectiveCamera(36, width / canvasHeight, 0.5, 600);
    cameraRef.current = camera;

    // 2. High-Quality WebGL Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      preserveDrawingBuffer: true,
      powerPreference: 'high-performance',
    });
    rendererRef.current = renderer;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, canvasHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    dom.innerHTML = '';
    dom.appendChild(renderer.domElement);

    // 3. Studio Lighting (Directional Sun + Ambient Sky)
    const hemiLight = new THREE.HemisphereLight(0xffffff, 0xe2e8f0, 0.85);
    scene.add(hemiLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 1.85);
    sunLight.position.set(38, 55, -28);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 1;
    sunLight.shadow.camera.far = 250;
    sunLight.shadow.camera.left = -45;
    sunLight.shadow.camera.right = 45;
    sunLight.shadow.camera.top = 45;
    sunLight.shadow.camera.bottom = -45;
    sunLight.shadow.bias = -0.0004;
    scene.add(sunLight);

    const softFillLight = new THREE.DirectionalLight(0xbfdbfe, 0.55);
    softFillLight.position.set(-35, 40, 35);
    scene.add(softFillLight);

    // 4. Ground Shadow Receiver Plane
    const groundGeo = new THREE.PlaneGeometry(300, 300);
    const groundMat = new THREE.ShadowMaterial({ opacity: 0.14 });
    const groundMesh = new THREE.Mesh(groundGeo, groundMat);
    groundMesh.rotation.x = -Math.PI / 2;
    groundMesh.position.y = -0.05;
    groundMesh.receiveShadow = true;
    scene.add(groundMesh);

    // 5. Extract Dimensions & Active Floor Geometry
    const siteW = Number(candidate?.siteWidth || candidate?.siteBoundary?.width || 30);
    const siteD = Number(candidate?.siteDepth || candidate?.siteBoundary?.depth || 40);
    const bldgX = Number(candidate?.buildingBoundary?.x || 2);
    const bldgY = Number(candidate?.buildingBoundary?.y || 3);
    const bldgW = Number(candidate?.buildingBoundary?.width || siteW - 4);
    const bldgD = Number(candidate?.buildingBoundary?.depth || siteD - 5);

    const floorGeom = candidate?.floorsGeometry?.[activeFloorIdx] || candidate?.floorsGeometry?.[0];
    const rooms = (floorGeom?.rooms && floorGeom.rooms.length > 0)
      ? floorGeom.rooms
      : (candidate?.rooms || []).filter((r) => (r.floor || 0) === activeFloorIdx);

    const style = RENDER_STYLES[renderStyle] || RENDER_STYLES.photorealistic;
    const cutawayH = 4.8; // half-height cutaway walls in feet

    // Centering offsets
    const centerX = siteW / 2;
    const centerZ = siteD / 2;
    camSphericalRef.current.targetX = 0;
    camSphericalRef.current.targetY = cutawayH * 0.45;
    camSphericalRef.current.targetZ = 0;

    const maxDim = Math.max(siteW, siteD, 35);
    const preset = VIEW_ANGLES[viewAngle] || VIEW_ANGLES.birds_eye;
    camSphericalRef.current.radius = maxDim * (preset.radiusMult || 1.25);

    // 6. Base Foundation Slab
    const slabThick = 0.7;
    const slabGeo = new THREE.BoxGeometry(bldgW + 0.8, slabThick, bldgD + 0.8);
    const slabMat = new THREE.MeshStandardMaterial({
      color: style.slabColor,
      roughness: 0.6,
    });
    const slabMesh = new THREE.Mesh(slabGeo, slabMat);
    slabMesh.position.set(bldgX + bldgW / 2 - centerX, -slabThick / 2, bldgY + bldgD / 2 - centerZ);
    slabMesh.receiveShadow = true;
    slabMesh.castShadow = true;
    scene.add(slabMesh);

    // 7. Individual Room Floor Slabs with PBR Textures
    rooms.forEach((r) => {
      const rw = Number(r.width) || 10;
      const rd = Number(r.height || r.depth) || 10;
      const rx = Number(r.x) || 0;
      const rz = Number(r.y) || 0;
      const type = (r.type || r.name || '').toLowerCase();

      let floorTex = null;
      if (type.includes('kitchen') || type.includes('dining')) {
        floorTex = createMarbleTileTexture(renderStyle);
      } else if (type.includes('bath') || type.includes('wc') || type.includes('toilet')) {
        floorTex = createCeramicMosaicTexture(renderStyle);
      } else if (type.includes('balcony') || type.includes('verandah') || type.includes('deck')) {
        floorTex = createBalconyDeckTexture(renderStyle);
      } else {
        floorTex = createWoodPlankTexture(type, renderStyle);
      }

      floorTex.repeat.set(Math.max(1, Math.round(rw / 6)), Math.max(1, Math.round(rd / 6)));

      const roomSlabGeo = new THREE.BoxGeometry(rw - 0.1, 0.12, rd - 0.1);
      const roomSlabMat = new THREE.MeshStandardMaterial({
        map: floorTex,
        roughness: type.includes('kitchen') ? 0.2 : 0.5,
        metalness: 0.05,
      });
      const roomSlab = new THREE.Mesh(roomSlabGeo, roomSlabMat);
      const roomCenterX = rx + rw / 2 - centerX;
      const roomCenterZ = rz + rd / 2 - centerZ;
      roomSlab.position.set(roomCenterX, 0.06, roomCenterZ);
      roomSlab.receiveShadow = true;
      scene.add(roomSlab);

      // Add 3D furniture inside each room
      const furnGroup = buildRoomFurnitureGroup(r, renderStyle);
      furnGroup.position.set(roomCenterX, 0.12, roomCenterZ);
      scene.add(furnGroup);
    });

    // 8. Extrude Architectural Cutaway Walls with Charcoal Top Wall Caps
    const wallCapMat = new THREE.MeshStandardMaterial({
      color: style.wallCapColor,
      roughness: 0.35,
    });
    const wallMat = new THREE.MeshStandardMaterial({
      color: style.wallColor,
      roughness: 0.8,
    });

    // Extract wall segments from floorGeom.walls or room perimeters
    const wallSegments = floorGeom?.walls && floorGeom.walls.length > 0
      ? floorGeom.walls
      : rooms.flatMap((r) => {
          const rx = Number(r.x) || 0;
          const ry = Number(r.y) || 0;
          const rw = Number(r.width) || 10;
          const rh = Number(r.height || r.depth) || 10;
          return [
            { start: { x: rx, y: ry }, end: { x: rx + rw, y: ry }, wallType: 'interior' },
            { start: { x: rx + rw, y: ry }, end: { x: rx + rw, y: ry + rh }, wallType: 'interior' },
            { start: { x: rx, y: ry + rh }, end: { x: rx + rw, y: ry + rh }, wallType: 'interior' },
            { start: { x: rx, y: ry }, end: { x: rx, y: ry + rh }, wallType: 'interior' },
          ];
        });

    wallSegments.forEach((w, wIdx) => {
      const x1 = w.start.x - centerX;
      const z1 = w.start.y - centerZ;
      const x2 = w.end.x - centerX;
      const z2 = w.end.y - centerZ;

      const dx = x2 - x1;
      const dz = z2 - z1;
      const len = Math.hypot(dx, dz);
      if (len < 0.8) return;

      const angle = Math.atan2(dz, dx);
      const isExt = w.wallType === 'exterior';
      const thick = isExt ? 0.65 : 0.38;

      // Wall Body
      const wGeo = new THREE.BoxGeometry(len, cutawayH, thick);
      const wMesh = new THREE.Mesh(wGeo, wallMat);
      wMesh.position.set(x1 + dx / 2, cutawayH / 2, z1 + dz / 2);
      wMesh.rotation.y = -angle;
      wMesh.castShadow = true;
      wMesh.receiveShadow = true;
      scene.add(wMesh);

      // Dark Wall Cap on top (matching floor-plan.ai signature architectural cutaway)
      const capGeo = new THREE.BoxGeometry(len + 0.04, 0.12, thick + 0.08);
      const capMesh = new THREE.Mesh(capGeo, wallCapMat);
      capMesh.position.set(x1 + dx / 2, cutawayH + 0.06, z1 + dz / 2);
      capMesh.rotation.y = -angle;
      scene.add(capMesh);
    });

    // 9. Windows (glazing planes on exterior apertures)
    (floorGeom?.windows || []).forEach((win) => {
      const isH = win.orientation === 'horizontal';
      const wLen = win.width || 3.5;
      const wx = win.x - centerX;
      const wz = win.y - centerZ;

      const glassGeo = new THREE.BoxGeometry(isH ? wLen : 0.15, 2.8, isH ? 0.15 : wLen);
      const glassMat = new THREE.MeshStandardMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.5,
        roughness: 0.1,
      });
      const glassMesh = new THREE.Mesh(glassGeo, glassMat);
      glassMesh.position.set(wx, 1.8, wz);
      scene.add(glassMesh);
    });

    // 10. Smooth Camera Animation & Orbit Controls
    let isDragging = false;
    let dragMode = 'orbit'; // 'orbit' | 'pan'
    let lastX = 0;
    let lastY = 0;

    const onPointerDown = (e) => {
      isDragging = true;
      dragMode = e.button === 2 ? 'pan' : 'orbit';
      lastX = e.clientX;
      lastY = e.clientY;
    };

    const onPointerMove = (e) => {
      if (!isDragging) return;
      const deltaX = e.clientX - lastX;
      const deltaY = e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;

      const sph = camSphericalRef.current;
      if (dragMode === 'orbit') {
        sph.theta -= deltaX * 0.007;
        sph.phi = Math.max(0.08, Math.min(Math.PI * 0.46, sph.phi + deltaY * 0.007));
      } else {
        const panSpeed = sph.radius * 0.0016;
        sph.targetX -= (Math.cos(sph.theta) * deltaX - Math.sin(sph.theta) * deltaY) * panSpeed;
        sph.targetZ += (Math.sin(sph.theta) * deltaX + Math.cos(sph.theta) * deltaY) * panSpeed;
      }
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    const onWheel = (e) => {
      e.preventDefault();
      const sph = camSphericalRef.current;
      sph.radius = Math.max(12, Math.min(180, sph.radius + e.deltaY * 0.04));
    };

    const onContextMenu = (e) => e.preventDefault();

    dom.addEventListener('mousedown', onPointerDown);
    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);
    dom.addEventListener('wheel', onWheel, { passive: false });
    dom.addEventListener('contextmenu', onContextMenu);

    // Render loop
    const animate = () => {
      animIdRef.current = requestAnimationFrame(animate);

      const sph = camSphericalRef.current;
      if (autoRotate && !isDragging) {
        sph.theta += 0.003;
      }

      // Convert spherical coordinates to cartesian position
      const cx = sph.targetX + sph.radius * Math.sin(sph.phi) * Math.sin(sph.theta);
      const cy = sph.targetY + sph.radius * Math.cos(sph.phi);
      const cz = sph.targetZ + sph.radius * Math.sin(sph.phi) * Math.cos(sph.theta);

      camera.position.set(cx, cy, cz);
      camera.lookAt(sph.targetX, sph.targetY, sph.targetZ);

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!dom || !rendererRef.current || !cameraRef.current) return;
      const w = dom.clientWidth || 800;
      cameraRef.current.aspect = w / canvasHeight;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, canvasHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animIdRef.current);
      dom.removeEventListener('mousedown', onPointerDown);
      window.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('mouseup', onPointerUp);
      dom.removeEventListener('wheel', onWheel);
      dom.removeEventListener('contextmenu', onContextMenu);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
    };
  }, [candidate, activeFloorIdx, renderStyle, viewAngle, bgMode, height, autoRotate]);

  const handleDownloadSnapshot = () => {
    if (!rendererRef.current) return;
    const dataUrl = rendererRef.current.domElement.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = `${candidate?.code || 'floorplan'}-3d-dollhouse-${renderStyle}.png`;
    link.href = dataUrl;
    link.click();
  };

  const setCameraPreset = (angleKey) => {
    setViewAngle(angleKey);
    const preset = VIEW_ANGLES[angleKey];
    if (preset) {
      camSphericalRef.current.theta = preset.theta;
      camSphericalRef.current.phi = preset.phi;
    }
  };

  const bgHex = BG_MODES[bgMode]?.bg || '#FFFFFF';

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: `${height}px`,
        background: bgHex,
        borderRadius: '12px',
        overflow: 'hidden',
        userSelect: 'none',
      }}
    >
      {/* 3D WebGL Canvas Mount */}
      <div
        ref={mountRef}
        style={{ width: '100%', height: `${height}px`, cursor: 'grab' }}
      />

      {/* Floating Bottom Navigation Bar */}
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          left: '14px',
          right: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '8px',
          pointerEvents: 'none',
          flexWrap: 'wrap',
        }}
      >
        {/* Left: Style & Angle Badge */}
        <span
          style={{
            background: 'rgba(15, 23, 42, 0.82)',
            backdropFilter: 'blur(6px)',
            color: '#FFFFFF',
            fontSize: '11px',
            fontWeight: 600,
            padding: '4px 11px',
            borderRadius: '999px',
          }}
        >
          ✨ {RENDER_STYLES[renderStyle]?.label} · {VIEW_ANGLES[viewAngle]?.label} · 3D Dollhouse
        </span>

        {/* Right: Quick Camera Presets & Download Button */}
        <div style={{ display: 'flex', gap: '5px', pointerEvents: 'auto' }}>
          {[
            { id: 'birds_eye', label: "Bird's Eye" },
            { id: 'angled', label: 'Angled 3D' },
            { id: 'room_focused', label: 'Close-Up' },
          ].map((cam) => (
            <button
              key={cam.id}
              type="button"
              onClick={() => setCameraPreset(cam.id)}
              style={{
                padding: '4px 9px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '999px',
                border: viewAngle === cam.id ? '1px solid #2563EB' : '1px solid #CBD5E1',
                background: viewAngle === cam.id ? '#EFF6FF' : 'rgba(255, 255, 255, 0.94)',
                color: viewAngle === cam.id ? '#2563EB' : '#1E293B',
                cursor: 'pointer',
                boxShadow: '0 1px 3px rgba(15,23,42,0.06)',
              }}
            >
              {cam.label}
            </button>
          ))}

          <button
            type="button"
            onClick={() => setAutoRotate(!autoRotate)}
            style={{
              padding: '4px 9px',
              fontSize: '11px',
              fontWeight: 600,
              borderRadius: '999px',
              border: '1px solid #CBD5E1',
              background: autoRotate ? '#EFF6FF' : 'rgba(255, 255, 255, 0.94)',
              color: autoRotate ? '#2563EB' : '#1E293B',
              cursor: 'pointer',
            }}
          >
            {autoRotate ? '⟳ Rotating' : '⟳ 360°'}
          </button>

          <button
            type="button"
            onClick={handleDownloadSnapshot}
            style={{
              padding: '4px 10px',
              fontSize: '11px',
              fontWeight: 700,
              borderRadius: '999px',
              border: '1px solid #BFDBFE',
              background: '#EFF6FF',
              color: '#1D4ED8',
              cursor: 'pointer',
              boxShadow: '0 1px 3px rgba(15,23,42,0.06)',
            }}
          >
            ↓ 3D PNG
          </button>
        </div>
      </div>
    </div>
  );
}
