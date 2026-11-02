"""LuminaLab Swarm - Universal Diagram Engine (SVG/Interactive Nodes)."""

import json
import math
from src.contracts.schemas import SimulationSpec, EngineType


def _is_arabic(text: str) -> bool:
    """Check if the text contains Arabic characters."""
    return any('\u0600' <= ch <= '\u06FF' for ch in text)


def render_diagram_lab(spec: SimulationSpec) -> str:
    """
    Renders an interactive SVG diagram micro-lab for network, circuit, and anatomical concepts.

    Parameters:
        spec: SimulationSpec with engine_type=EngineType.DIAGRAM.

    Returns:
        A self-contained HTML5 string (<25KB) with inline SVG, CSS, and JS.

    Raises:
        ValueError: If engine_type is not DIAGRAM or nodes has fewer than 2 items.
    """
    if spec.engine_type != EngineType.DIAGRAM:
        raise ValueError("Expected DIAGRAM engine type")

    if not spec.nodes or len(spec.nodes) < 2:
        raise ValueError("DIAGRAM engine requires at least two nodes")

    # Detect language direction
    is_ar = _is_arabic(spec.title) or any(_is_arabic(n.get("label", "")) for n in spec.nodes)
    direction = "rtl" if is_ar else "ltr"
    lang = "ar" if is_ar else "en"

    # Localization
    info_placeholder = "انقر على أي عقدة في المخطط لعرض بياناتها وعلاقاتها" if is_ar else "Click on any node in the diagram to inspect its connections."
    connections_label = "المتصلات:" if is_ar else "Connected to:"
    node_word = "العقدة:" if is_ar else "Node:"

    # Compute node positions if not properly set
    has_custom_coords = any(n.get("x", 0) != 0 or n.get("y", 0) != 0 for n in spec.nodes)
    nodes_data = []

    if has_custom_coords:
        # Scale coords to fit 500x320 box with margins
        min_x = min(n.get("x", 0) for n in spec.nodes)
        max_x = max(n.get("x", 0) for n in spec.nodes)
        min_y = min(n.get("y", 0) for n in spec.nodes)
        max_y = max(n.get("y", 0) for n in spec.nodes)

        span_x = max_x - min_x if max_x > min_x else 1
        span_y = max_y - min_y if max_y > min_y else 1

        for n in spec.nodes:
            norm_x = 70 + ((n.get("x", 0) - min_x) / span_x) * 360
            norm_y = 60 + ((n.get("y", 0) - min_y) / span_y) * 200
            nodes_data.append({
                "id": str(n.get("id")),
                "label": str(n.get("label", n.get("id"))),
                "x": round(norm_x, 1),
                "y": round(norm_y, 1),
                "connections": [str(c) for c in n.get("connections", [])]
            })
    else:
        # Circular distribution
        total_n = len(spec.nodes)
        cx, cy, rx, ry = 250, 160, 160, 100
        for i, n in enumerate(spec.nodes):
            angle = (2 * math.pi * i) / total_n - (math.pi / 2)
            nx = cx + rx * math.cos(angle)
            ny = cy + ry * math.sin(angle)
            nodes_data.append({
                "id": str(n.get("id")),
                "label": str(n.get("label", n.get("id"))),
                "x": round(nx, 1),
                "y": round(ny, 1),
                "connections": [str(c) for c in n.get("connections", [])]
            })

    # Build node map for fast coordinate lookup
    node_map = {n["id"]: n for n in nodes_data}

    # Generate SVG Lines
    svg_lines = []
    drawn_pairs = set()

    for n in nodes_data:
        from_id = n["id"]
        x1, y1 = n["x"], n["y"]
        for to_id in n["connections"]:
            if to_id in node_map:
                pair_key = tuple(sorted([from_id, to_id]))
                to_node = node_map[to_id]
                x2, y2 = to_node["x"], to_node["y"]
                line_el = f'<line class="conn-line" data-from="{from_id}" data-to="{to_id}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" />'
                svg_lines.append(line_el)
                drawn_pairs.add(pair_key)

    lines_html = "\n".join(svg_lines)

    # Generate SVG Nodes
    svg_nodes = []
    for n in nodes_data:
        nid = n["id"]
        lbl = n["label"]
        nx, ny = n["x"], n["y"]
        node_el = f"""
        <g class="diagram-node" id="node-{nid}" data-id="{nid}" onclick="selectNode('{nid}')" transform="translate({nx},{ny})">
            <circle class="node-circle" r="26" />
            <text class="node-text" dy="5" text-anchor="middle">{lbl}</text>
        </g>
        """
        svg_nodes.append(node_el)

    nodes_svg_html = "\n".join(svg_nodes)
    nodes_json = json.dumps(nodes_data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec.title}</title>
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --primary: #2563eb;
            --primary-light: #eff6ff;
            --highlight: #f59e0b;
            --line-color: #94a3b8;
            --text-main: #0f172a;
            --text-muted: #64748b;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
        }}
        body {{
            background: var(--bg-color);
            color: var(--text-main);
            padding: 20px;
            font-size: 16px;
            line-height: 1.5;
        }}
        .lab-container {{
            max-width: 650px;
            margin: 0 auto;
            background: var(--card-bg);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08);
            border: 1px solid #e2e8f0;
        }}
        h1 {{
            font-size: 24px;
            color: var(--primary);
            text-align: center;
            margin-bottom: 16px;
        }}
        .svg-card {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
        }}
        svg {{
            width: 100%;
            height: auto;
            max-height: 360px;
        }}
        .conn-line {{
            stroke: var(--line-color);
            stroke-width: 3;
            stroke-dasharray: 4;
            transition: all 0.3s ease;
        }}
        .conn-line.active {{
            stroke: var(--highlight);
            stroke-width: 5;
            stroke-dasharray: none;
        }}
        .diagram-node {{
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        .diagram-node:hover {{
            transform: scale(1.08);
        }}
        .node-circle {{
            fill: var(--primary-light);
            stroke: var(--primary);
            stroke-width: 3;
            transition: all 0.3s ease;
        }}
        .diagram-node.active .node-circle {{
            fill: #fef3c7;
            stroke: var(--highlight);
            stroke-width: 4;
            filter: drop-shadow(0 4px 6px rgba(245, 158, 11, 0.35));
        }}
        .node-text {{
            font-size: 13px;
            font-weight: 700;
            fill: var(--text-main);
            pointer-events: none;
            user-select: none;
        }}
        .info-card {{
            background: #f1f5f9;
            border-radius: 12px;
            padding: 16px 20px;
            border: 1px solid #cbd5e1;
            min-height: 70px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .info-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 4px;
        }}
        .info-conn {{
            font-size: 14px;
            color: var(--text-muted);
        }}
        .conn-badge {{
            display: inline-block;
            background: #e2e8f0;
            padding: 2px 8px;
            border-radius: 4px;
            margin: 2px 4px;
            font-weight: 600;
            color: var(--text-main);
        }}
    </style>
</head>
<body>
    <div class="lab-container">
        <h1>{spec.title}</h1>

        <div class="svg-card">
            <svg viewBox="0 0 500 320">
                <g id="lines-layer">
                    {lines_html}
                </g>
                <g id="nodes-layer">
                    {nodes_svg_html}
                </g>
            </svg>
        </div>

        <div class="info-card" id="info-card">
            <div id="info-text">{info_placeholder}</div>
        </div>
    </div>

    <script>
        const nodesData = {nodes_json};
        const nodeMap = {{}};
        nodesData.forEach(n => {{ nodeMap[n.id] = n; }});

        const nodeWord = "{node_word}";
        const connLabel = "{connections_label}";

        function selectNode(id) {{
            const selected = nodeMap[id];
            if (!selected) return;

            // Highlight node
            document.querySelectorAll('.diagram-node').forEach(el => {{
                el.classList.remove('active');
            }});
            const nodeEl = document.getElementById('node-' + id);
            if (nodeEl) nodeEl.classList.add('active');

            // Highlight lines connected to or from this node
            document.querySelectorAll('.conn-line').forEach(line => {{
                const f = line.getAttribute('data-from');
                const t = line.getAttribute('data-to');
                if (f === id || t === id) {{
                    line.classList.add('active');
                }} else {{
                    line.classList.remove('active');
                }}
            }});

            // Update Info Card
            const card = document.getElementById('info-card');
            const conns = selected.connections || [];
            let connsHtml = '';
            if (conns.length > 0) {{
                connsHtml = conns.map(cid => {{
                    const target = nodeMap[cid];
                    const label = target ? target.label : cid;
                    return '<span class="conn-badge">' + label + '</span>';
                }}).join(' ');
            }} else {{
                connsHtml = '<span class="conn-badge">-</span>';
            }}

            card.innerHTML = `
                <div class="info-title">${{nodeWord}} ${{selected.label}}</div>
                <div class="info-conn">${{connLabel}} ${{connsHtml}}</div>
            `;
        }}

        // Auto select first node
        if (nodesData.length > 0) {{
            selectNode(nodesData[0].id);
        }}
    </script>
</body>
</html>"""
    return html
