"""
ZYNORA AI — Deterministic 2D CAD Floor Plan SVG Renderer
=========================================================
Generates vector-accurate, architectural SVG blueprints directly from
the structured floorplan JSON geometry.

Supports:
  - Plot & building setback boundaries
  - Room fills with distinct architectural styling
  - Room names, dimensions, and area labels
  - Exterior (9-inch) & interior (4.5-inch) wall linework
  - Accessible doors with 90° swing arcs
  - Window fenestrations with architectural double-lines
  - Staircase treads with flight direction arrows
  - Structural columns
  - Dimension tick lines & leader annotations
  - 2D CAD furniture symbols (beds, sofas, tables, counters, sanitary fixtures)
  - Auspicious North-arrow orientation compass
  - Architectural title block / stamp
"""
import math
from typing import Dict, Any, List, Optional


ROOM_FILL_COLORS = {
    "living": "#f8fafc",
    "family_living": "#f8fafc",
    "drawing": "#f1f5f9",
    "dining": "#fefce8",
    "kitchen": "#fffbeb",
    "bedroom": "#faf5ff",
    "master_bedroom": "#f3e8ff",
    "bathroom": "#f0f9ff",
    "common_bathroom": "#f0f9ff",
    "attached_bathroom": "#e0f2fe",
    "pooja": "#fff7ed",
    "study": "#fdf4ff",
    "office": "#fdf4ff",
    "utility": "#f4f4f5",
    "balcony": "#f0fdf4",
    "terrace": "#ecfdf5",
    "courtyard": "#ecfdf5",
    "circulation": "#ffffff",
    "staircase": "#f8fafc",
    "parking": "#f4f4f5",
}


def render_floorplan_to_svg(
    floorplan: Dict[str, Any],
    floor_idx: int = 0,
    width_px: int = 1200,
    height_px: int = 900,
) -> str:
    """
    Renders an editable, high-resolution SVG blueprint from a floorplan candidate.
    """
    site_b = floorplan.get("siteBoundary", {}) or {}
    site_w = max(20.0, float(site_b.get("width", 30.0)))
    site_d = max(25.0, float(site_b.get("depth", 40.0)))
    orientation = str(site_b.get("entranceDirection") or floorplan.get("orientation") or "East")

    floors_geom = floorplan.get("floorsGeometry", [])
    fl_data = (
        floors_geom[floor_idx]
        if floor_idx < len(floors_geom)
        else (floors_geom[0] if floors_geom else {})
    )

    rooms = fl_data.get("rooms", floorplan.get("rooms", []))
    walls = fl_data.get("walls", [])
    doors = fl_data.get("doors", [])
    windows = fl_data.get("windows", [])
    stairs = fl_data.get("stairs", [])
    columns = fl_data.get("columns", [])
    dimensions = fl_data.get("dimensions", [])
    furniture_blocks = fl_data.get("furnitureBlocks", [])

    # Setup SVG coordinate system with margins
    margin = 4.0
    view_x = -margin
    view_y = -margin
    view_w = site_w + (margin * 2.0)
    view_h = site_d + (margin * 2.0)

    svg_parts: List[str] = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view_x:.2f} {view_y:.2f} {view_w:.2f} {view_h:.2f}" '
        f'width="{width_px}" height="{height_px}" style="background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;">'
    )

    # 1. Defs: Hatch patterns, markers, and filters
    svg_parts.append("""
    <defs>
        <pattern id="grid" width="2" height="2" patternUnits="userSpaceOnUse">
            <path d="M 2 0 L 0 0 0 2" fill="none" stroke="#f1f5f9" stroke-width="0.08"/>
        </pattern>
        <pattern id="brickHatch" width="1.5" height="0.8" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0.4" x2="1.5" y2="0.4" stroke="#94a3b8" stroke-width="0.06"/>
            <line x1="0.75" y1="0" x2="0.75" y2="0.4" stroke="#94a3b8" stroke-width="0.06"/>
            <line x1="1.5" y1="0.4" x2="1.5" y2="0.8" stroke="#94a3b8" stroke-width="0.06"/>
        </pattern>
        <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#0284c7" />
        </marker>
    </defs>
    """)

    # 2. Background Grid
    svg_parts.append(f'<rect x="{view_x:.2f}" y="{view_y:.2f}" width="{view_w:.2f}" height="{view_h:.2f}" fill="url(#grid)" />')

    # 3. Site Boundary (Plot Line)
    svg_parts.append(
        f'<rect x="0" y="0" width="{site_w:.2f}" height="{site_d:.2f}" '
        f'fill="none" stroke="#64748b" stroke-width="0.25" stroke-dasharray="0.8, 0.4" />'
    )
    svg_parts.append(
        f'<text x="{site_w / 2:.2f}" y="-1.2" text-anchor="middle" font-size="1.1" font-weight="600" fill="#64748b">'
        f'ROAD FRONTAGE ({site_w:g}\' 0")</text>'
    )

    # 4. Room Fills and Borders
    for r in rooms:
        rx = float(r.get("x", 0.0))
        ry = float(r.get("y", 0.0))
        rw = float(r.get("width", 10.0))
        rh = float(r.get("height", 10.0))
        rtype = str(r.get("type", "bedroom")).lower()
        rname = str(r.get("name", rtype.title()))
        rarea = int(r.get("area", round(rw * rh)))
        fill_col = ROOM_FILL_COLORS.get(rtype, "#f8fafc")

        # Room polygon / rectangle
        svg_parts.append(
            f'<rect x="{rx:.2f}" y="{ry:.2f}" width="{rw:.2f}" height="{rh:.2f}" '
            f'fill="{fill_col}" stroke="#cbd5e1" stroke-width="0.12" />'
        )

        # Room Label and Dimensions
        cx = rx + (rw / 2.0)
        cy = ry + (rh / 2.0)
        svg_parts.append(
            f'<g class="room-label" style="pointer-events: none;">'
            f'<text x="{cx:.2f}" y="{cy - 0.4:.2f}" text-anchor="middle" font-size="0.95" font-weight="700" fill="#1e293b">{rname}</text>'
            f'<text x="{cx:.2f}" y="{cy + 0.6:.2f}" text-anchor="middle" font-size="0.75" font-weight="500" fill="#64748b">{rw:g}\' × {rh:g}\'</text>'
            f'<text x="{cx:.2f}" y="{cy + 1.4:.2f}" text-anchor="middle" font-size="0.65" font-weight="600" fill="#94a3b8">{rarea} sq ft</text>'
            f'</g>'
        )

    # 5. Furniture CAD Blocks
    for furn in furniture_blocks:
        fx = float(furn.get("x", 0.0))
        fy = float(furn.get("y", 0.0))
        fw = float(furn.get("width", 3.0))
        fh = float(furn.get("height", 3.0))
        ftype = str(furn.get("type", "")).lower()

        if "bed" in ftype:
            # Bed outline with pillows
            svg_parts.append(f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{fw:.2f}" height="{fh:.2f}" rx="0.3" fill="#ffffff" stroke="#94a3b8" stroke-width="0.15" />')
            svg_parts.append(f'<rect x="{fx + 0.3:.2f}" y="{fy + 0.3:.2f}" width="{fw * 0.4:.2f}" height="1.2" rx="0.2" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="0.08" />')
            svg_parts.append(f'<rect x="{fx + fw * 0.55:.2f}" y="{fy + 0.3:.2f}" width="{fw * 0.4:.2f}" height="1.2" rx="0.2" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="0.08" />')
        elif "sofa" in ftype or "living" in ftype:
            svg_parts.append(f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{fw:.2f}" height="{fh:.2f}" rx="0.4" fill="#f8fafc" stroke="#94a3b8" stroke-width="0.15" />')
        elif "dining" in ftype or "table" in ftype:
            svg_parts.append(f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{fw:.2f}" height="{fh:.2f}" rx="0.5" fill="#ffffff" stroke="#94a3b8" stroke-width="0.15" />')
        else:
            svg_parts.append(f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{fw:.2f}" height="{fh:.2f}" fill="#ffffff" stroke="#cbd5e1" stroke-width="0.1" />')

    # 6. Walls (Solid Linework with Architectural Thickness)
    for w in walls:
        p1 = w.get("p1", [0, 0])
        p2 = w.get("p2", [0, 0])
        is_ext = bool(w.get("isExterior", False))
        stroke_w = "0.70" if is_ext else "0.35"
        stroke_col = "#0f172a" if is_ext else "#334155"
        svg_parts.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="{stroke_col}" stroke-width="{stroke_w}" stroke-linecap="square" />'
        )

    # 7. Doors with 90° Swing Arcs
    for d in doors:
        pos = d.get("position", [0, 0])
        dw = float(d.get("width", 3.0))
        dx, dy = pos[0], pos[1]
        svg_parts.append(
            f'<line x1="{dx:.2f}" y1="{dy:.2f}" x2="{dx + dw:.2f}" y2="{dy:.2f}" stroke="#0f172a" stroke-width="0.25" />'
        )
        # Swing arc
        svg_parts.append(
            f'<path d="M {dx + dw:.2f} {dy:.2f} A {dw:.2f} {dw:.2f} 0 0 1 {dx:.2f} {dy + dw:.2f}" '
            f'fill="none" stroke="#94a3b8" stroke-width="0.12" stroke-dasharray="0.3, 0.2" />'
        )

    # 8. Windows with Architectural Double Lines
    for win in windows:
        p1 = win.get("p1") or win.get("position") or [0, 0]
        p2 = win.get("p2") or [p1[0] + float(win.get("width", 4.0)), p1[1]]
        svg_parts.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="#0284c7" stroke-width="0.45" />'
        )
        svg_parts.append(
            f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" '
            f'stroke="#ffffff" stroke-width="0.15" />'
        )

    # 9. Staircase with Steps and Flight Arrow
    for st in stairs:
        sx = float(st.get("x", 0.0))
        sy = float(st.get("y", 0.0))
        sw = float(st.get("width", 6.0))
        sh = float(st.get("height", 10.0))
        steps = int(st.get("stepCount", 12))
        step_h = sh / max(1, steps)

        svg_parts.append(f'<rect x="{sx:.2f}" y="{sy:.2f}" width="{sw:.2f}" height="{sh:.2f}" fill="#f8fafc" stroke="#334155" stroke-width="0.2" />')
        for s_i in range(1, steps):
            line_y = sy + (s_i * step_h)
            svg_parts.append(f'<line x1="{sx:.2f}" y1="{line_y:.2f}" x2="{sx + sw:.2f}" y2="{line_y:.2f}" stroke="#94a3b8" stroke-width="0.1" />')

        # Direction Arrow & UP label
        mid_x = sx + (sw / 2.0)
        svg_parts.append(
            f'<line x1="{mid_x:.2f}" y1="{sy + sh - 1.0:.2f}" x2="{mid_x:.2f}" y2="{sy + 1.0:.2f}" '
            f'stroke="#0284c7" stroke-width="0.2" marker-end="url(#arrow)" />'
        )
        svg_parts.append(f'<text x="{mid_x + 0.4:.2f}" y="{sy + sh - 1.2:.2f}" font-size="0.7" font-weight="700" fill="#0284c7">UP</text>')

    # 10. Structural Columns
    for col in columns:
        cx = float(col.get("x", 0.0))
        cy = float(col.get("y", 0.0))
        cw = float(col.get("width", 0.75))
        ch = float(col.get("height", 0.75))
        svg_parts.append(
            f'<rect x="{cx - cw / 2:.2f}" y="{cy - ch / 2:.2f}" width="{cw:.2f}" height="{ch:.2f}" fill="#1e293b" />'
        )

    # 11. Dimension Ticks & Annotations
    if isinstance(dimensions, dict):
        bw_label = dimensions.get("buildingWidthLabel")
        bd_label = dimensions.get("buildingDepthLabel")
        if bw_label:
            svg_parts.append(f'<text x="{site_w / 2:.2f}" y="{site_d + 1.8:.2f}" text-anchor="middle" font-size="0.75" font-weight="600" fill="#64748b">Width: {bw_label}</text>')
        if bd_label:
            svg_parts.append(f'<text x="-1.8" y="{site_d / 2:.2f}" text-anchor="middle" transform="rotate(-90, -1.8, {site_d / 2:.2f})" font-size="0.75" font-weight="600" fill="#64748b">Depth: {bd_label}</text>')
    elif isinstance(dimensions, list):
        for dim in dimensions:
            if isinstance(dim, dict):
                p1 = dim.get("p1", [0, 0])
                p2 = dim.get("p2", [0, 0])
                label = str(dim.get("text", ""))
                mid_x = (p1[0] + p2[0]) / 2.0
                mid_y = (p1[1] + p2[1]) / 2.0
                svg_parts.append(f'<line x1="{p1[0]:.2f}" y1="{p1[1]:.2f}" x2="{p2[0]:.2f}" y2="{p2[1]:.2f}" stroke="#94a3b8" stroke-width="0.08" />')
                if label:
                    svg_parts.append(f'<text x="{mid_x:.2f}" y="{mid_y - 0.2:.2f}" text-anchor="middle" font-size="0.65" fill="#64748b">{label}</text>')

    # 12. North Arrow / Orientation Compass in Top-Right
    compass_x = site_w - 2.5
    compass_y = 2.5
    svg_parts.append(f"""
    <g transform="translate({compass_x:.2f}, {compass_y:.2f})">
        <circle cx="0" cy="0" r="1.8" fill="#ffffff" stroke="#cbd5e1" stroke-width="0.1" />
        <!-- North Arrow Needle -->
        <polygon points="0,-1.5 0.5,0 0,0" fill="#dc2626" />
        <polygon points="0,-1.5 -0.5,0 0,0" fill="#ef4444" />
        <polygon points="0,1.5 0.5,0 0,0" fill="#64748b" />
        <polygon points="0,1.5 -0.5,0 0,0" fill="#94a3b8" />
        <text x="0" y="-1.9" text-anchor="middle" font-size="0.8" font-weight="800" fill="#dc2626">N</text>
        <text x="0" y="2.5" text-anchor="middle" font-size="0.55" font-weight="600" fill="#64748b">{orientation.upper()}</text>
    </g>
    """)

    # 13. Title Block / Seal in Bottom-Right
    total_area = round(sum(float(r.get("area", 0)) for r in rooms))
    cand_title = floorplan.get("title", "ZyNora Residence")
    cand_code = floorplan.get("code", "Candidate A")
    fl_label = "Ground Floor" if floor_idx == 0 else f"Level {floor_idx}"

    tb_w = 12.0
    tb_h = 3.5
    tb_x = site_w - tb_w
    tb_y = site_d + 0.3
    svg_parts.append(f"""
    <g transform="translate({tb_x:.2f}, {tb_y:.2f})">
        <rect x="0" y="0" width="{tb_w:.2f}" height="{tb_h:.2f}" fill="#ffffff" stroke="#94a3b8" stroke-width="0.15" />
        <rect x="0" y="0" width="{tb_w:.2f}" height="0.9" fill="#0f172a" />
        <text x="0.6" y="0.65" font-size="0.55" font-weight="800" fill="#ffffff">ZYNORA AI ARCHITECTURAL STUDIO</text>
        <text x="0.6" y="1.6" font-size="0.65" font-weight="700" fill="#0f172a">{cand_title} ({cand_code})</text>
        <text x="0.6" y="2.3" font-size="0.55" font-weight="500" fill="#475569">{fl_label} · Built-Up: {total_area:g} sq ft · Plot: {site_w:g}\'×{site_d:g}\'</text>
        <text x="0.6" y="3.0" font-size="0.5" font-weight="600" fill="#0284c7">Deterministic AI CAD Blueprint · 1/4" = 1\'-0" Metric</text>
    </g>
    """)

    svg_parts.append("</svg>")
    return "".join(svg_parts)
