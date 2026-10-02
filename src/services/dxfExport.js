/**
 * AutoCAD .DXF Vector Exporter for Architectural Floorplans
 * ==========================================================
 * Generates an industry-standard AutoCAD Release 12 (AC1009) .DXF file
 * containing:
 *  - Layer definitions (WALLS_EXTERNAL, WALLS_INTERNAL, ROOM_LABELS, DIMENSIONS, VASTU_COMPASS)
 *  - Closed 2D polylines for exterior envelope and individual rooms
 *  - Room name & square footage text entities
 *  - Dimension annotations & Vastu cardinal axis markers
 */

export function generateFloorplanDXF(candidate, project) {
  const projName = project?.name || 'Zynora Villa';
  const candName = candidate?.code || 'Candidate A';
  const candTitle = candidate?.title || 'Residential Floorplan';
  const totalArea = candidate?.area || 2400;
  const rooms = candidate?.rooms || [];
  const floorsGeo = candidate?.floorsGeometry || [];

  let dxf = '';

  // 1. SECTION HEADER
  dxf += '0\nSECTION\n2\nHEADER\n';
  dxf += '9\n$ACADVER\n1\nAC1009\n';
  dxf += '9\n$INSUNITS\n70\n2\n'; // 2 = Feet
  dxf += '0\nENDSEC\n';

  // 2. SECTION TABLES (Layer definitions)
  dxf += '0\nSECTION\n2\nTABLES\n0\nTABLE\n2\nLAYER\n70\n10\n';
  dxf += '0\nLAYER\n2\n0\n70\n0\n62\n7\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nSITE_BOUNDARY\n70\n0\n62\n8\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nWALLS_EXTERNAL\n70\n0\n62\n4\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nWALLS_INTERNAL\n70\n0\n62\n3\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nDOORS\n70\n0\n62\n30\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nWINDOWS\n70\n0\n62\n5\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nSTAIRS\n70\n0\n62\n6\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nCOLUMNS\n70\n0\n62\n1\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nROOM_LABELS\n70\n0\n62\n2\n6\nCONTINUOUS\n';
  dxf += '0\nLAYER\n2\nDIMENSIONS\n70\n0\n62\n1\n6\nCONTINUOUS\n';
  dxf += '0\nENDTAB\n0\nENDSEC\n';

  // 3. SECTION ENTITIES
  dxf += '0\nSECTION\n2\nENTITIES\n';

  function polyline(layer, coords) {
    let out = `0\nPOLYLINE\n8\n${layer}\n66\n1\n70\n1\n`;
    coords.forEach(([x, y]) => {
      out += `0\nVERTEX\n8\n${layer}\n10\n${Number(x).toFixed(3)}\n20\n${Number(y).toFixed(3)}\n30\n0.0\n`;
    });
    out += '0\nSEQEND\n';
    return out;
  }

  function text(layer, content, x, y, height = 0.85, align = 0) {
    return `0\nTEXT\n8\n${layer}\n10\n${Number(x).toFixed(3)}\n20\n${Number(y).toFixed(3)}\n30\n0.0\n40\n${height}\n1\n${content}\n72\n${align}\n`;
  }

  function line(layer, x1, y1, x2, y2) {
    return `0\nLINE\n8\n${layer}\n10\n${Number(x1).toFixed(3)}\n20\n${Number(y1).toFixed(3)}\n30\n0.0\n11\n${Number(x2).toFixed(3)}\n21\n${Number(y2).toFixed(3)}\n31\n0.0\n`;
  }

  if (floorsGeo.length > 0) {
    // Export true 16-stage multi-floor 2D CAD geometry side-by-side (in feet)
    floorsGeo.forEach((fg, fIdx) => {
      const sb = fg.siteBoundary || { x: 0, y: 0, width: 30, height: 40 };
      const offsetX = fIdx * (sb.width + 14);
      const flipY = (yVal) => sb.height - yVal;

      // Floor header
      dxf += text('ROOM_LABELS', `${(fg.label || `FLOOR ${fg.floor}`).toUpperCase()} (${sb.width}' x ${sb.height}')`, offsetX, sb.height + 4.0, 1.1);
      dxf += text('DIMENSIONS', `PROJECT: ${projName.toUpperCase()} | ${candName} (${candTitle.toUpperCase()})`, offsetX, sb.height + 2.2, 0.75);

      // Site Boundary
      dxf += polyline('SITE_BOUNDARY', [
        [offsetX + 0, 0],
        [offsetX + sb.width, 0],
        [offsetX + sb.width, sb.height],
        [offsetX + 0, sb.height],
        [offsetX + 0, 0]
      ]);

      // Walls
      (fg.walls || []).forEach((w) => {
        const layer = w.type === 'exterior' ? 'WALLS_EXTERNAL' : 'WALLS_INTERNAL';
        dxf += line(layer, offsetX + w.x1, flipY(w.y1), offsetX + w.x2, flipY(w.y2));
      });

      // Doors
      (fg.doors || []).forEach((d) => {
        const dw = d.width || 3.0;
        if (d.orientation === 'H') {
          dxf += line('DOORS', offsetX + d.x - dw / 2, flipY(d.y), offsetX + d.x + dw / 2, flipY(d.y));
        } else {
          dxf += line('DOORS', offsetX + d.x, flipY(d.y - dw / 2), offsetX + d.x, flipY(d.y + dw / 2));
        }
      });

      // Windows
      (fg.windows || []).forEach((win) => {
        const ww = win.width || 4.0;
        if (win.orientation === 'H') {
          dxf += line('WINDOWS', offsetX + win.x - ww / 2, flipY(win.y), offsetX + win.x + ww / 2, flipY(win.y));
        } else {
          dxf += line('WINDOWS', offsetX + win.x, flipY(win.y - ww / 2), offsetX + win.x, flipY(win.y + ww / 2));
        }
      });

      // Structural Columns
      (fg.columns || []).forEach((col) => {
        const hs = (col.size || 0.75) / 2;
        const cx = offsetX + col.x;
        const cy = flipY(col.y);
        dxf += polyline('COLUMNS', [
          [cx - hs, cy - hs],
          [cx + hs, cy - hs],
          [cx + hs, cy + hs],
          [cx - hs, cy + hs],
          [cx - hs, cy - hs]
        ]);
      });

      // Staircase
      if (fg.staircase) {
        const st = fg.staircase;
        const sx1 = offsetX + st.x;
        const sy1 = flipY(st.y + st.height);
        const sx2 = sx1 + st.width;
        const sy2 = flipY(st.y);
        dxf += polyline('STAIRS', [
          [sx1, sy1], [sx2, sy1], [sx2, sy2], [sx1, sy2], [sx1, sy1]
        ]);
        const steps = st.steps || 10;
        for (let s = 1; s < steps; s++) {
          const ty = sy1 + ((sy2 - sy1) * s) / steps;
          dxf += line('STAIRS', sx1, ty, sx2, ty);
        }
      }

      // Rooms & Open Spaces Labels + Polylines
      [...(fg.rooms || []), ...(fg.openSpaces || [])].forEach((rm) => {
        const rx1 = offsetX + rm.x;
        const ry1 = flipY(rm.y + rm.height);
        const rx2 = rx1 + rm.width;
        const ry2 = flipY(rm.y);
        dxf += polyline('WALLS_INTERNAL', [
          [rx1, ry1], [rx2, ry1], [rx2, ry2], [rx1, ry2], [rx1, ry1]
        ]);
        dxf += text('ROOM_LABELS', (rm.name || rm.type || 'ROOM').toUpperCase(), rx1 + 0.6, (ry1 + ry2) / 2 + 0.4, 0.65);
        dxf += text('DIMENSIONS', `${rm.width}' x ${rm.height}' (${rm.area} SQFT)`, rx1 + 0.6, (ry1 + ry2) / 2 - 0.5, 0.48);
      });
    });
  } else {
    // Fallback legacy grid when floorsGeometry is absent
    const widthM = 40;
    const lengthM = 30;
    dxf += polyline('WALLS_EXTERNAL', [
      [0, 0], [widthM, 0], [widthM, lengthM], [0, lengthM], [0, 0]
    ]);
    dxf += text('ROOM_LABELS', `PROJECT: ${projName.toUpperCase()} - ${candName}`, 0, lengthM + 2.2, 0.9);
    const cols = 3;
    const rows = Math.max(2, Math.ceil(rooms.length / cols));
    const pad = 0.5;
    const cellW = (widthM - (cols + 1) * pad) / cols;
    const cellH = (lengthM - (rows + 1) * pad) / rows;
    rooms.forEach((rm, i) => {
      const col = i % cols;
      const row = Math.floor(i / cols);
      const x1 = pad + col * (cellW + pad);
      const y1 = lengthM - pad - (row + 1) * (cellH + pad);
      dxf += polyline('WALLS_INTERNAL', [
        [x1, y1], [x1 + cellW, y1], [x1 + cellW, y1 + cellH], [x1, y1 + cellH], [x1, y1]
      ]);
      dxf += text('ROOM_LABELS', rm.name.toUpperCase(), x1 + 0.5, y1 + cellH / 2 + 0.3, 0.55);
      dxf += text('DIMENSIONS', `${rm.area} SQ FT`, x1 + 0.5, y1 + cellH / 2 - 0.4, 0.45);
    });
  }

  // End DXF
  dxf += '0\nENDSEC\n0\nEOF\n';
  return dxf;
}

export function downloadFloorplanDXF(candidate, project) {
  try {
    const dxfString = generateFloorplanDXF(candidate, project);
    const blob = new Blob([dxfString], { type: 'application/dxf;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const safeCode = (candidate?.code || 'Candidate').replace(/\s+/g, '_');
    link.href = url;
    link.download = `Zynora_${safeCode}_Architectural_Floorplan.dxf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    return { success: true };
  } catch (err) {
    console.error('Failed to export DXF:', err);
    return { success: false, error: err.message };
  }
}
