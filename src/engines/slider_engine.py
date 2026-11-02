"""LuminaLab Swarm - Universal Hybrid Slider & Interactive Physics Engine (HTML5/SVG)."""

import json
import math

import re
from typing import Any
from src.contracts.schemas import SimulationSpec, EngineType



def _clean_num(val: float) -> str:
    """Format floating point numbers without floating point representation noise or zeroing out scientific notation."""
    if val == 0:
        return "0"
    if val == int(val):
        return str(int(val))
    abs_v = abs(val)
    if abs_v < 1e-3 or abs_v > 1e5:
        return f"{val:.4g}"
    formatted = f"{val:.4f}".rstrip("0").rstrip(".")
    return formatted if formatted else "0"





def _symbol_in_expr(sym: str, expr: str) -> bool:
    """Check if a variable symbol is functionally referenced inside an expression."""
    if not sym or not expr:
        return False
    clean_sym = sym.strip()
    if clean_sym.startswith("[") and clean_sym.endswith("]"):
        inner = clean_sym[1:-1].strip()
        if clean_sym in expr:
            return True
        if inner and _symbol_in_expr(inner, expr):
            return True
        return False
    pattern = r'(?<![a-zA-Z0-9_\u0600-\u06FF])' + re.escape(clean_sym) + r'(?![a-zA-Z0-9_\u0600-\u06FF])'
    return bool(re.search(pattern, expr, re.IGNORECASE))



def _is_variable_active(var: dict, active_expr: str, svg_bindings: dict | None, archetype: str) -> bool:
    """Determine if a variable actively impacts calculation or visual animation."""
    sym = var.get("symbol", "")
    if not sym:
        return False
    if _symbol_in_expr(sym, active_expr):
        return True
    if svg_bindings and sym in svg_bindings:
        return True
    return False


def _is_arabic(text: str) -> bool:
    """Check if the text contains Arabic characters."""
    return any('\u0600' <= ch <= '\u06FF' for ch in text)


def _detect_archetype(spec: SimulationSpec) -> str:
    """Detect or validate visual archetype for the simulation spec."""
    raw = str(getattr(spec, "visual_archetype", "") or "").strip().lower()
    from src.swarm.pair2_interactive import VALID_ARCHETYPES, _infer_visual_archetype
    alias_map = {
        "cell": "cell_osmosis",
        "osmosis": "cell_osmosis",
        "lever": "lever_torque",
        "torque": "lever_torque",
        "titration": "ph_titration",
        "ph": "ph_titration",
        "poh": "ph_titration",
        "buffer": "ph_titration",
        "fission": "cell_division",
        "mitosis": "cell_division",
        "bacteria": "cell_division",
        "colony": "cell_division",
        "enzyme": "enzyme_kinetics",
        "michaelis": "enzyme_kinetics",
        "menten": "enzyme_kinetics",
        "calorimeter": "thermo_calorimeter",
        "calorimetry": "thermo_calorimeter",
        "thermo": "thermo_calorimeter",
        "dna": "dna_pcr",
        "pcr": "dna_pcr",
        "wave": "wave_oscillator",
        "gravity": "gravity_orbit",
        "orbit": "gravity_orbit",
        "block": "kinematics_block",
        "kinematics": "kinematics_block",
        "optics": "optics_bench",
        "lens": "optics_bench",
    }
    raw = alias_map.get(raw, raw)
    if raw in VALID_ARCHETYPES:
        return raw
    syms = [str(v.get("symbol", "")) for v in spec.variables if isinstance(v, dict)]
    return _infer_visual_archetype(
        topic=spec.title,
        formula=spec.formula_expression,
        var_symbols=syms
    )


def _render_archetype_svg(archetype: str, is_ar: bool = False) -> str:
    """Renders the authentic built-in SVG markup for a given visual archetype."""
    if archetype == "spring":
        return """
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Hooke's Law Spring Simulation">
                <rect x="130" y="8" width="100" height="8" rx="2" fill="#475569"/>
                <line x1="140" y1="8" x2="135" y2="2" stroke="#64748b" stroke-width="2"/>
                <line x1="160" y1="8" x2="155" y2="2" stroke="#64748b" stroke-width="2"/>
                <line x1="180" y1="8" x2="175" y2="2" stroke="#64748b" stroke-width="2"/>
                <line x1="200" y1="8" x2="195" y2="2" stroke="#64748b" stroke-width="2"/>
                <line x1="220" y1="8" x2="215" y2="2" stroke="#64748b" stroke-width="2"/>
                <g id="spring-ruler" transform="translate(262, 16)">
                    <rect x="0" y="0" width="28" height="116" rx="3" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
                    <line x1="0" y1="10" x2="10" y2="10" stroke="#64748b" stroke-width="1.5"/>
                    <text x="13" y="13" font-size="8" fill="#64748b" font-family="monospace">0</text>
                    <line x1="0" y1="35" x2="8" y2="35" stroke="#94a3b8" stroke-width="1"/>
                    <line x1="0" y1="60" x2="12" y2="60" stroke="#64748b" stroke-width="1.5"/>
                    <text x="14" y="63" font-size="8" fill="#64748b" font-family="monospace">.2</text>
                    <line x1="0" y1="85" x2="8" y2="85" stroke="#94a3b8" stroke-width="1"/>
                    <line x1="0" y1="110" x2="12" y2="110" stroke="#64748b" stroke-width="1.5"/>
                    <text x="14" y="113" font-size="8" fill="#64748b" font-family="monospace">.5m</text>
                </g>
                <line x1="90" y1="46" x2="260" y2="46" stroke="#94a3b8" stroke-dasharray="3,3" stroke-width="1"/>
                <text x="85" y="49" font-size="8" fill="#94a3b8" text-anchor="end">x₀</text>
                <path id="spring-coil-path" d="M 180,16 L 180,24 Q 162,28 180,32 Q 198,36 180,40 Q 162,44 180,48 Q 198,52 180,56 L 180,62"
                      fill="none" stroke="#4f46e5" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
                <g id="spring-mass-group" transform="translate(0, 0)" style="transition: transform 0.12s ease-out;">
                    <path d="M 180,62 C 180,68 174,70 174,73 C 174,76 186,76 186,73" fill="none" stroke="#475569" stroke-width="3"/>
                    <rect x="154" y="74" width="52" height="30" rx="5" fill="#f59e0b" stroke="#d97706" stroke-width="2"/>
                    <text id="mass-label" x="180" y="93" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">F = 10 N</text>
                    <polygon points="206,89 260,89 254,86 260,89 254,92" fill="#ef4444" stroke="#ef4444" stroke-width="2"/>
                    <circle cx="206" cy="89" r="3" fill="#ef4444"/>
                </g>
            </svg>
        </div>"""

    elif archetype == "beaker":
        conc_txt = "تركيز المحلول" if is_ar else "Concentration"
        state_title = "حالة المحلول" if is_ar else "Solution State"
        vol_txt = "الحجم" if is_ar else "Volume"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Chemistry Solution Beaker">
                <defs>
                    <linearGradient id="beaker-chem-grad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#93c5fd"/>
                        <stop offset="100%" stop-color="#1d4ed8"/>
                    </linearGradient>
                </defs>
                <rect x="110" y="20" width="130" height="110" rx="8" fill="#f8fafc" stroke="#94a3b8" stroke-width="2.5" opacity="0.3"/>
                <rect id="beaker-liquid" x="113" y="60" width="124" height="67" rx="6" fill="url(#beaker-chem-grad)" fill-opacity="0.65" style="transition: fill-opacity 0.25s, height 0.2s, y 0.2s;"/>
                <path d="M 102,20 L 248,20 M 102,20 L 108,28 M 248,20 L 242,28" stroke="#64748b" stroke-width="3" stroke-linecap="round"/>
                <line x1="115" y1="40" x2="132" y2="40" stroke="#64748b" stroke-width="1.5"/>
                <text x="136" y="43" font-size="8" fill="#64748b" font-family="monospace">250mL</text>
                <line x1="115" y1="65" x2="128" y2="65" stroke="#64748b" stroke-width="1"/>
                <text x="132" y="68" font-size="8" fill="#64748b" font-family="monospace">150mL</text>
                <line x1="115" y1="90" x2="132" y2="90" stroke="#64748b" stroke-width="1.5"/>
                <text x="136" y="93" font-size="8" fill="#64748b" font-family="monospace">50mL</text>
                <path d="M 110,22 L 110,122 Q 110,130 118,130 L 232,130 Q 240,130 240,122 L 240,22" fill="none" stroke="#475569" stroke-width="3"/>
                <g id="beaker-solute-particles">
                    <circle cx="140" cy="85" r="3" fill="#ffffff" opacity="0.75"/>
                    <circle cx="170" cy="100" r="3" fill="#ffffff" opacity="0.65"/>
                    <circle cx="195" cy="80" r="3" fill="#ffffff" opacity="0.8"/>
                    <circle cx="155" cy="112" r="3.5" fill="#ffffff" opacity="0.7"/>
                    <circle cx="215" cy="105" r="3" fill="#ffffff" opacity="0.75"/>
                    <circle cx="180" cy="72" r="2.5" fill="#ffffff" opacity="0.6"/>
                </g>
                <g transform="translate(252, 28)">
                    <rect x="0" y="0" width="98" height="84" rx="8" fill="#1e293b" stroke="#334155" stroke-width="1.5"/>
                    <text x="49" y="18" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="bold">{conc_txt}</text>
                    <text id="beaker-conc-val" x="49" y="36" font-size="12" fill="#38bdf8" text-anchor="middle" font-weight="800">1.00 M</text>
                    <line x1="8" y1="44" x2="90" y2="44" stroke="#334155" stroke-width="1"/>
                    <text id="beaker-state-badge" x="49" y="58" font-size="9" fill="#10b981" text-anchor="middle" font-weight="bold">Standard</text>
                    <text id="beaker-vol-val" x="49" y="74" font-size="8" fill="#64748b" text-anchor="middle">V = 150 mL</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "circuit":
        return """
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Ohm's Law Electric Circuit">
                <rect x="60" y="30" width="240" height="80" rx="8" fill="none" stroke="#64748b" stroke-width="4"/>
                <rect x="52" y="52" width="16" height="36" fill="#ffffff"/>
                <line x1="48" y1="60" x2="72" y2="60" stroke="#ef4444" stroke-width="4"/>
                <text x="38" y="63" font-size="10" font-weight="bold" fill="#ef4444">+</text>
                <line x1="54" y1="76" x2="66" y2="76" stroke="#1e293b" stroke-width="4"/>
                <text x="40" y="80" font-size="10" font-weight="bold" fill="#1e293b">−</text>
                <text id="battery-label" x="25" y="72" font-size="11" font-weight="bold" fill="#64748b" text-anchor="end">V</text>
                <rect x="145" y="106" width="70" height="8" fill="#ffffff"/>
                <path d="M 145,110 L 150,102 L 160,118 L 170,102 L 180,118 L 190,102 L 200,118 L 205,102 L 210,110" fill="none" stroke="#d97706" stroke-width="3" stroke-linejoin="round"/>
                <text id="resistor-label" x="180" y="132" font-size="10" font-weight="bold" fill="#d97706" text-anchor="middle">R</text>
                <g transform="translate(180, 30)">
                    <rect x="-20" y="-4" width="40" height="8" fill="#ffffff"/>
                    <circle id="bulb-glow" cx="0" cy="0" r="22" fill="#fbbf24" opacity="0.4" style="transition: opacity 0.2s, r 0.2s;"/>
                    <circle cx="0" cy="0" r="14" fill="#fef3c7" stroke="#92400e" stroke-width="2"/>
                    <path d="M -5,6 L -2,-4 L 2,-4 L 5,6" fill="none" stroke="#d97706" stroke-width="1.5"/>
                </g>
                <g transform="translate(300, 70)">
                    <circle cx="0" cy="0" r="15" fill="#f8fafc" stroke="#3b82f6" stroke-width="2"/>
                    <text x="0" y="4" font-size="10" font-weight="bold" fill="#3b82f6" text-anchor="middle">A</text>
                    <text id="current-label" x="22" y="4" font-size="11" font-weight="bold" fill="#3b82f6">0.0 A</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "piston":
        return """
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Gas Cylinder Piston">
                <rect x="50" y="20" width="170" height="105" rx="6" fill="#1e293b" opacity="0.08"/>
                <path d="M 50,20 L 50,125 L 220,125 L 220,20" fill="none" stroke="#475569" stroke-width="4"/>
                <g id="gas-chamber">
                    <circle cx="80" cy="95" r="3" fill="#3b82f6"/>
                    <circle cx="110" cy="112" r="3" fill="#3b82f6"/>
                    <circle cx="135" cy="90" r="3" fill="#3b82f6"/>
                    <circle cx="165" cy="108" r="3" fill="#3b82f6"/>
                    <circle cx="190" cy="95" r="3" fill="#3b82f6"/>
                </g>
                <g id="piston-assembly" transform="translate(0, 0)" style="transition: transform 0.15s ease-out;">
                    <rect x="130" y="0" width="10" height="40" fill="#94a3b8" stroke="#475569" stroke-width="2"/>
                    <rect x="54" y="38" width="162" height="16" rx="2" fill="#64748b" stroke="#334155" stroke-width="2"/>
                </g>
                <g id="piston-gauge">
                    <circle cx="268" cy="55" r="22" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>
                    <path d="M 253,55 A 15,15 0 0,1 283,55" fill="none" stroke="#ef4444" stroke-width="2"/>
                    <line id="piston-gauge-needle" x1="268" y1="55" x2="268" y2="39" stroke="#ef4444" stroke-width="2" stroke-linecap="round"/>
                    <circle cx="268" cy="55" r="3" fill="#1e293b"/>
                    <text id="piston-pressure-text" x="268" y="71" font-size="8.5" font-weight="bold" fill="#64748b" text-anchor="middle">P</text>
                </g>
            </svg>
        </div>"""

    elif archetype in ("cell_osmosis", "cell"):
        ext_label = "محلول خارج خلوي" if is_ar else "Extracellular Solution"
        iso_label = "متعادل" if is_ar else "Isotonic"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Cell Membrane Osmosis Simulation">
                <rect x="50" y="15" width="260" height="110" rx="16" fill="#f0f9ff" stroke="#bae6fd" stroke-width="2"/>
                <text x="65" y="32" font-size="9" fill="#0284c7" font-weight="bold">{ext_label}</text>
                <g transform="translate(180, 70)">
                    <ellipse id="cell-membrane" cx="0" cy="0" rx="60" ry="42" fill="#fdf4ff" stroke="#c084fc" stroke-width="3" style="transition: rx 0.2s, ry 0.2s;"/>
                    <circle cx="-5" cy="0" r="16" fill="#a855f7" opacity="0.6"/>
                    <circle cx="-5" cy="0" r="6" fill="#6b21a8" opacity="0.8"/>
                </g>
                <g transform="translate(245, 95)">
                    <rect x="0" y="0" width="60" height="24" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
                    <text id="cell-state-label" x="30" y="16" font-size="9" font-weight="bold" fill="#9333ea" text-anchor="middle">{iso_label}</text>
                </g>
            </svg>
        </div>"""

    elif archetype in ("lever_torque", "lever"):
        effort_text = "الجهد" if is_ar else "Effort"
        load_text = "الحمل" if is_ar else "Load"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Interactive Lever Simulation">
                <rect x="130" y="90" width="100" height="8" rx="4" fill="#94a3b8"/>
                <polygon points="180,56 164,90 196,90" fill="#475569"/>
                <circle cx="180" cy="56" r="4" fill="#f8fafc" stroke="#334155" stroke-width="2"/>
                <g id="lever-beam-group" style="transition: transform 0.15s ease-out; transform-origin: 180px 56px;">
                    <rect x="25" y="52" width="310" height="8" rx="4" fill="#3b82f6"/>
                    <line x1="180" y1="48" x2="180" y2="64" stroke="#ffffff" stroke-width="2"/>
                    <rect id="weight-left" x="50" y="28" width="34" height="24" rx="4" fill="#10b981"/>
                    <text id="text-left" x="67" y="44" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">{effort_text}</text>
                    <rect id="weight-right" x="276" y="22" width="38" height="30" rx="4" fill="#f59e0b"/>
                    <text id="text-right" x="295" y="41" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">{load_text}</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "spectrophotometer":
        sample_txt = "عينة المحلول" if is_ar else "Liquid Sample"
        abs_txt = "الامتصاصية" if is_ar else "Absorbance"
        trans_txt = "النفاذية" if is_ar else "Transmittance"
        stat_txt = "الحالة" if is_ar else "Status"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Spectrophotometer Simulation">
                <defs>
                    <linearGradient id="beam-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.9"/>
                        <stop offset="100%" stop-color="#818cf8" stop-opacity="0.9"/>
                    </linearGradient>
                    <linearGradient id="cuvette-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#ffffff" stop-opacity="0.5"/>
                        <stop offset="100%" stop-color="#cbd5e1" stop-opacity="0.2"/>
                    </linearGradient>
                </defs>
                <rect x="15" y="15" width="330" height="110" rx="10" fill="#0f172a" stroke="#334155" stroke-width="2"/>
                <rect x="25" y="45" width="40" height="50" rx="6" fill="#1e293b" stroke="#475569" stroke-width="1.5"/>
                <circle cx="45" cy="70" r="14" fill="#fbbf24" opacity="0.3"/>
                <circle cx="45" cy="70" r="8" fill="#fef08a"/>
                <text x="45" y="106" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="bold">Light</text>
                <line id="beam-incident" x1="65" y1="70" x2="140" y2="70" stroke="url(#beam-grad)" stroke-width="7" stroke-linecap="round"/>
                <text x="100" y="62" font-size="9" fill="#38bdf8" text-anchor="middle" font-weight="bold">I₀</text>
                <rect x="136" y="35" width="6" height="30" fill="#475569"/>
                <rect x="136" y="75" width="6" height="30" fill="#475569"/>
                <rect x="150" y="32" width="44" height="76" rx="4" fill="url(#cuvette-grad)" stroke="#94a3b8" stroke-width="1.5"/>
                <rect id="cuvette-liquid" x="153" y="35" width="38" height="70" rx="2" fill="#3b82f6" opacity="0.6" style="transition: opacity 0.25s, fill 0.25s;"/>
                <text x="172" y="27" font-size="8" fill="#cbd5e1" text-anchor="middle">{sample_txt}</text>
                <line id="beam-transmitted" x1="194" y1="70" x2="255" y2="70" stroke="#818cf8" stroke-width="5" stroke-linecap="round" opacity="0.6" style="transition: opacity 0.25s, stroke-width 0.25s;"/>
                <text x="225" y="62" font-size="9" fill="#818cf8" text-anchor="middle" font-weight="bold">I</text>
                <rect x="255" y="50" width="16" height="40" rx="3" fill="#1e293b" stroke="#6366f1" stroke-width="2"/>
                <g transform="translate(280, 30)">
                    <rect x="0" y="0" width="55" height="80" rx="6" fill="#1e293b" stroke="#475569" stroke-width="1.5"/>
                    <text x="27" y="16" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="bold">{abs_txt}</text>
                    <text id="spectro-abs-val" x="27" y="32" font-size="12" fill="#38bdf8" text-anchor="middle" font-weight="800">0.00</text>
                    <line x1="6" y1="38" x2="49" y2="38" stroke="#334155" stroke-width="1"/>
                    <text x="27" y="50" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="bold">{trans_txt}</text>
                    <text id="spectro-trans-val" x="27" y="66" font-size="11" fill="#10b981" text-anchor="middle" font-weight="800">100%</text>
                </g>
                <text id="spectro-status" x="172" y="122" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="bold">{stat_txt}: OK</text>
            </svg>
        </div>"""

    elif archetype == "optics_bench":
        obj_txt = "الجسم" if is_ar else "Object"
        img_txt = "الصورة" if is_ar else "Image"
        lens_txt = "عدسة محدبة" if is_ar else "Convex Lens"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Optics Bench Simulation">
                <line x1="15" y1="70" x2="345" y2="70" stroke="#64748b" stroke-width="1.5" stroke-dasharray="4,4"/>
                <rect x="15" y="120" width="330" height="10" rx="3" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"/>
                <line x1="60" y1="120" x2="60" y2="126" stroke="#94a3b8" stroke-width="1"/>
                <line x1="120" y1="120" x2="120" y2="126" stroke="#94a3b8" stroke-width="1"/>
                <line x1="180" y1="120" x2="180" y2="130" stroke="#4f46e5" stroke-width="2"/>
                <line x1="240" y1="120" x2="240" y2="126" stroke="#94a3b8" stroke-width="1"/>
                <line x1="300" y1="120" x2="300" y2="126" stroke="#94a3b8" stroke-width="1"/>
                <circle cx="130" cy="70" r="3" fill="#ef4444"/>
                <text x="130" y="84" font-size="8" fill="#ef4444" text-anchor="middle" font-weight="bold">F₁</text>
                <circle cx="230" cy="70" r="3" fill="#ef4444"/>
                <text x="230" y="84" font-size="8" fill="#ef4444" text-anchor="middle" font-weight="bold">F₂</text>
                <g transform="translate(180, 70)">
                    <ellipse cx="0" cy="0" rx="9" ry="48" fill="#e0f2fe" stroke="#0284c7" stroke-width="2" opacity="0.8"/>
                    <path d="M 0,-52 L -5,-44 M 0,-52 L 5,-44" stroke="#0284c7" stroke-width="2"/>
                    <path d="M 0,52 L -5,44 M 0,52 L 5,44" stroke="#0284c7" stroke-width="2"/>
                </g>
                <text x="180" y="16" font-size="9" fill="#0284c7" text-anchor="middle" font-weight="bold">{lens_txt}</text>
                <path id="ray-parallel" d="M 70,35 L 180,35 L 290,105" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="2,2"/>
                <path id="ray-central" d="M 70,35 L 180,70 L 290,105" fill="none" stroke="#3b82f6" stroke-width="1.5"/>
                <g id="optics-object-group" transform="translate(70, 70)" style="transition: transform 0.2s ease-out;">
                    <line x1="0" y1="0" x2="0" y2="-35" stroke="#10b981" stroke-width="3"/>
                    <polygon points="0,-40 -4,-32 4,-32" fill="#10b981"/>
                    <text x="0" y="14" font-size="9" fill="#10b981" text-anchor="middle" font-weight="bold">{obj_txt}</text>
                </g>
                <g id="optics-image-group" transform="translate(290, 70)" style="transition: transform 0.2s ease-out;">
                    <line x1="0" y1="0" x2="0" y2="35" stroke="#f59e0b" stroke-width="3"/>
                    <polygon points="0,40 -4,32 4,32" fill="#f59e0b"/>
                    <text x="0" y="-8" font-size="9" fill="#f59e0b" text-anchor="middle" font-weight="bold">{img_txt}</text>
                </g>
                <g transform="translate(260, 16)">
                    <rect x="0" y="0" width="85" height="22" rx="4" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                    <text id="optics-nature-badge" x="42" y="15" font-size="8" fill="#4f46e5" text-anchor="middle" font-weight="bold">Real / Inverted</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "refraction":
        med1_txt = "وسط 1 (n₁)" if is_ar else "Medium 1 (n₁)"
        med2_txt = "وسط 2 (n₂)" if is_ar else "Medium 2 (n₂)"
        tir_txt = "انعكاس كلي" if is_ar else "Total Reflection"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Snell's Law Refraction Simulation">
                <rect x="20" y="10" width="320" height="60" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/>
                <text x="40" y="30" font-size="10" fill="#64748b" font-weight="bold">{med1_txt}</text>
                <rect x="20" y="70" width="320" height="60" fill="#e0f2fe" opacity="0.6"/>
                <text x="40" y="115" font-size="10" fill="#0284c7" font-weight="bold">{med2_txt}</text>
                <line x1="20" y1="70" x2="340" y2="70" stroke="#0284c7" stroke-width="2"/>
                <line x1="180" y1="15" x2="180" y2="125" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3"/>
                <circle cx="180" cy="70" r="45" fill="none" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="2,2"/>
                <line id="incident-ray" x1="135" y1="25" x2="180" y2="70" stroke="#eab308" stroke-width="3" stroke-linecap="round"/>
                <line id="refracted-ray" x1="180" y1="70" x2="225" y2="125" stroke="#06b6d4" stroke-width="3" stroke-linecap="round" style="transition: x2 0.15s, y2 0.15s;"/>
                <line id="reflected-ray" x1="180" y1="70" x2="225" y2="25" stroke="#ef4444" stroke-width="2" stroke-dasharray="4,2" opacity="0.3" style="transition: opacity 0.2s;"/>
                <g transform="translate(250, 18)">
                    <rect x="0" y="0" width="80" height="42" rx="6" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>
                    <text x="40" y="16" font-size="9" fill="#eab308" text-anchor="middle" font-weight="bold">θ₁ = <tspan id="angle-theta1-text">45°</tspan></text>
                    <text x="40" y="34" font-size="9" fill="#06b6d4" text-anchor="middle" font-weight="bold">θ₂ = <tspan id="angle-theta2-text">28°</tspan></text>
                </g>
                <g id="tir-badge-group" transform="translate(250, 85)" style="display: none;">
                    <rect x="0" y="0" width="80" height="22" rx="4" fill="#fee2e2" stroke="#ef4444" stroke-width="1"/>
                    <text id="tir-badge" x="40" y="15" font-size="8" fill="#b91c1c" text-anchor="middle" font-weight="bold">TIR / {tir_txt}</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "kinematics_block":
        force_txt = "قوة السحب" if is_ar else "Applied Force"
        fric_txt = "الاحتكاك" if is_ar else "Friction"
        acc_txt = "التسارع" if is_ar else "Acceleration"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Kinematics Newton Simulation">
                <defs>
                    <marker id="arrow-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981"/>
                    </marker>
                    <marker id="arrow-red" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 1 L 10 5 L 0 9 z" fill="#ef4444"/>
                    </marker>
                </defs>
                <rect x="20" y="100" width="320" height="14" rx="2" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1.5"/>
                <line x1="20" y1="114" x2="340" y2="114" stroke="#64748b" stroke-width="2"/>
                <line x1="30" y1="120" x2="40" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <line x1="70" y1="120" x2="80" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <line x1="110" y1="120" x2="120" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <line x1="150" y1="120" x2="160" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <line x1="190" y1="120" x2="200" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <line x1="230" y1="120" x2="240" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <line x1="270" y1="120" x2="280" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <line x1="310" y1="120" x2="320" y2="114" stroke="#cbd5e1" stroke-width="1"/>
                <g id="kinematics-block-group" transform="translate(140, 62)" style="transition: transform 0.2s ease-out;">
                    <rect x="0" y="0" width="65" height="38" rx="5" fill="#3b82f6" stroke="#1d4ed8" stroke-width="2"/>
                    <rect x="8" y="6" width="49" height="14" rx="2" fill="#60a5fa" opacity="0.4"/>
                    <text id="block-mass-label" x="32" y="25" fill="#ffffff" font-size="11" font-weight="bold" text-anchor="middle">m</text>
                    <line id="vector-force" x1="65" y1="19" x2="115" y2="19" stroke="#10b981" stroke-width="3" marker-end="url(#arrow-green)"/>
                    <line id="vector-friction" x1="0" y1="19" x2="-35" y2="19" stroke="#ef4444" stroke-width="3" marker-end="url(#arrow-red)"/>
                    <line x1="32" y1="0" x2="32" y2="-20" stroke="#64748b" stroke-width="1.5"/>
                    <polygon points="32,-24 29,-18 35,-18" fill="#64748b"/>
                    <line x1="32" y1="38" x2="32" y2="52" stroke="#64748b" stroke-width="1.5"/>
                    <polygon points="32,56 29,50 35,50" fill="#64748b"/>
                </g>
                <g transform="translate(20, 18)">
                    <rect x="0" y="0" width="105" height="40" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                    <text x="8" y="16" font-size="9" fill="#10b981" font-weight="bold">{force_txt}: <tspan id="force-val">10 N</tspan></text>
                    <text x="8" y="32" font-size="9" fill="#ef4444" font-weight="bold">{fric_txt}: <tspan id="friction-val">2 N</tspan></text>
                </g>
                <g transform="translate(235, 18)">
                    <rect x="0" y="0" width="105" height="40" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                    <text x="52" y="16" font-size="9" fill="#3b82f6" font-weight="bold" text-anchor="middle">{acc_txt}</text>
                    <text id="accel-val" x="52" y="32" font-size="12" fill="#1e293b" font-weight="800" text-anchor="middle">a = 0.00 m/s²</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "pendulum":
        ke_txt = "طاقة الحركة (KE)" if is_ar else "Kinetic (KE)"
        pe_txt = "طاقة الوضع (PE)" if is_ar else "Potential (PE)"
        period_txt = "الزمن الدوري" if is_ar else "Period (T)"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Simple Pendulum Simulation">
                <rect x="140" y="6" width="80" height="8" rx="2" fill="#475569"/>
                <circle cx="180" cy="14" r="5" fill="#1e293b" stroke="#94a3b8" stroke-width="2"/>
                <circle cx="180" cy="14" r="2" fill="#ffffff"/>
                <line x1="180" y1="14" x2="180" y2="125" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="3,3"/>
                <g id="pendulum-arm-group" style="transition: transform 0.15s ease-out; transform-origin: 180px 14px;">
                    <line id="pendulum-string" x1="180" y1="14" x2="180" y2="105" stroke="#475569" stroke-width="2"/>
                    <circle id="pendulum-bob" cx="180" cy="105" r="13" fill="#e11d48" stroke="#be123c" stroke-width="2"/>
                    <circle cx="176" cy="101" r="4" fill="#ffffff" opacity="0.4"/>
                </g>
                <g transform="translate(20, 30)">
                    <rect x="0" y="0" width="85" height="52" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                    <text x="42" y="16" font-size="8" fill="#64748b" text-anchor="middle" font-weight="bold">{period_txt}</text>
                    <text id="pendulum-period-val" x="42" y="32" font-size="11" fill="#4f46e5" text-anchor="middle" font-weight="800">1.42 s</text>
                    <text id="pendulum-angle-val" x="42" y="46" font-size="9" fill="#059669" text-anchor="middle" font-weight="bold">θ = 0°</text>
                </g>
                <g transform="translate(265, 25)">
                    <rect x="0" y="0" width="80" height="90" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                    <text x="22" y="16" font-size="8" fill="#10b981" text-anchor="middle" font-weight="bold">KE</text>
                    <rect x="14" y="22" width="16" height="50" rx="3" fill="#e2e8f0"/>
                    <rect id="bar-ke-fill" x="14" y="42" width="16" height="30" rx="3" fill="#10b981" style="transition: height 0.15s, y 0.15s;"/>
                    <text x="58" y="16" font-size="8" fill="#3b82f6" text-anchor="middle" font-weight="bold">PE</text>
                    <rect x="50" y="22" width="16" height="50" rx="3" fill="#e2e8f0"/>
                    <rect id="bar-pe-fill" x="50" y="52" width="16" height="20" rx="3" fill="#3b82f6" style="transition: height 0.15s, y 0.15s;"/>
                    <text x="40" y="84" font-size="7" fill="#94a3b8" text-anchor="middle">Energy</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "projectile":
        range_txt = "المدى الأفقي" if is_ar else "Max Range (R)"
        hmax_txt = "أقصى ارتفاع" if is_ar else "Peak Height (H)"
        time_txt = "زمن التحليق" if is_ar else "Flight Time (t)"
        launch_txt = "منصة الإطلاق" if is_ar else "Launcher"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Projectile Motion Simulation">
                <defs>
                    <linearGradient id="ground-grad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#334155"/>
                        <stop offset="100%" stop-color="#1e293b"/>
                    </linearGradient>
                </defs>
                <rect x="15" y="115" width="330" height="15" rx="3" fill="url(#ground-grad)"/>
                <line x1="15" y1="115" x2="345" y2="115" stroke="#10b981" stroke-width="2"/>
                <path id="trajectory-path" d="M 35,115 Q 160,20 285,115" fill="none" stroke="#38bdf8" stroke-width="2.5" stroke-dasharray="4,3"/>
                <circle cx="35" cy="115" r="9" fill="#475569" stroke="#1e293b" stroke-width="2"/>
                <g id="cannon-barrel" style="transition: transform 0.15s ease-out; transform-origin: 35px 115px;">
                    <rect x="27" y="111" width="26" height="8" rx="2" fill="#64748b" stroke="#334155" stroke-width="1.5"/>
                    <line x1="53" y1="111" x2="53" y2="119" stroke="#fbbf24" stroke-width="2"/>
                </g>
                <text x="35" y="136" font-size="8" fill="#94a3b8" text-anchor="middle">{launch_txt}</text>
                <circle id="projectile-ball" cx="160" cy="67" r="5" fill="#ef4444" stroke="#b91c1c" stroke-width="1.5"/>
                <g id="marker-peak" transform="translate(160, 67)">
                    <line x1="0" y1="0" x2="0" y2="48" stroke="#f59e0b" stroke-width="1" stroke-dasharray="2,2"/>
                    <circle cx="0" cy="0" r="2" fill="#f59e0b"/>
                </g>
                <g id="marker-range" transform="translate(285, 115)">
                    <polygon points="0,-4 -4,4 4,4" fill="#10b981"/>
                </g>
                <g transform="translate(225, 12)">
                    <rect x="0" y="0" width="120" height="58" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                    <text x="8" y="15" font-size="8" fill="#64748b" font-weight="bold">{range_txt}: <tspan id="telemetry-range" fill="#10b981">0.0 m</tspan></text>
                    <text x="8" y="28" font-size="8" fill="#64748b" font-weight="bold">{hmax_txt}: <tspan id="telemetry-hmax" fill="#38bdf8">0.0 m</tspan></text>
                    <text x="8" y="41" font-size="8" fill="#64748b" font-weight="bold">{time_txt}: <tspan id="telemetry-time" fill="#f59e0b">0.0 s</tspan></text>
                    <text id="telemetry-angle" x="8" y="53" font-size="8" fill="#4f46e5" font-weight="bold">θ = 45°</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "gravity_orbit":
        core_txt = "الجرم المركزي" if is_ar else "Central Mass"
        speed_txt = "السرعة المدارية" if is_ar else "Orbital Speed"
        rad_txt = "نصف القطر" if is_ar else "Radius"
        force_txt = "قوة الجاذبية" if is_ar else "Gravity Force"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Orbital Gravity Simulation">
                <defs>
                    <radialGradient id="sun-glow" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stop-color="#fef08a"/>
                        <stop offset="50%" stop-color="#f59e0b"/>
                        <stop offset="100%" stop-color="#b45309" stop-opacity="0.1"/>
                    </radialGradient>
                    <marker id="arrow-orbit-red" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                        <path d="M 0 1 L 10 5 L 0 9 z" fill="#ef4444"/>
                    </marker>
                    <marker id="arrow-orbit-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                        <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981"/>
                    </marker>
                </defs>
                <rect x="15" y="10" width="330" height="120" rx="10" fill="#0b0f19" stroke="#1e293b" stroke-width="1.5"/>
                <circle cx="50" cy="30" r="1" fill="#ffffff" opacity="0.6"/>
                <circle cx="100" cy="110" r="1.5" fill="#ffffff" opacity="0.4"/>
                <circle cx="280" cy="25" r="1" fill="#ffffff" opacity="0.5"/>
                <circle cx="310" cy="95" r="1" fill="#ffffff" opacity="0.7"/>
                <ellipse id="orbit-path" cx="170" cy="70" rx="95" ry="40" fill="none" stroke="#334155" stroke-width="1.5" stroke-dasharray="4,4"/>
                <circle cx="170" cy="70" r="26" fill="url(#sun-glow)"/>
                <circle cx="170" cy="70" r="16" fill="#f59e0b" stroke="#d97706" stroke-width="2"/>
                <text x="170" y="105" font-size="8" fill="#cbd5e1" text-anchor="middle" font-weight="bold">{core_txt}</text>
                <g id="orbiting-body" transform="translate(265, 70)">
                    <circle cx="0" cy="0" r="7" fill="#38bdf8" stroke="#0284c7" stroke-width="2"/>
                    <rect x="-14" y="-3" width="6" height="6" rx="1" fill="#0284c7"/>
                    <rect x="8" y="-3" width="6" height="6" rx="1" fill="#0284c7"/>
                    <line id="vector-gravity" x1="0" y1="0" x2="-25" y2="0" stroke="#ef4444" stroke-width="2" marker-end="url(#arrow-orbit-red)"/>
                    <line id="vector-velocity" x1="0" y1="0" x2="0" y2="-22" stroke="#10b981" stroke-width="2" marker-end="url(#arrow-orbit-green)"/>
                </g>
                <g transform="translate(25, 20)">
                    <rect x="0" y="0" width="85" height="52" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>
                    <text x="42" y="15" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="bold">{rad_txt}</text>
                    <text id="orbit-radius-val" x="42" y="28" font-size="10" fill="#38bdf8" text-anchor="middle" font-weight="800">1.0 m</text>
                    <line x1="6" y1="33" x2="79" y2="33" stroke="#334155" stroke-width="1"/>
                    <text id="orbit-speed-val" x="42" y="45" font-size="9" fill="#10b981" text-anchor="middle" font-weight="bold">30 km/s</text>
                </g>
                <text id="orbit-force-val" x="170" y="24" font-size="9" fill="#ef4444" text-anchor="middle" font-weight="bold">{force_txt}: 0.0 N</text>
            </svg>
        </div>"""

    elif archetype == "wave_oscillator":
        osc_txt = "المهتز" if is_ar else "Oscillator"
        speed_txt = "سرعة الموجة" if is_ar else "Wave Speed"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Wave Oscillator Simulation">
                <line x1="55" y1="70" x2="345" y2="70" stroke="#64748b" stroke-width="1.5" stroke-dasharray="3,3"/>
                <rect x="15" y="35" width="40" height="70" rx="6" fill="#1e293b" stroke="#475569" stroke-width="2"/>
                <g id="oscillator-piston" style="transition: transform 0.1s ease-out;">
                    <rect x="31" y="55" width="8" height="30" rx="2" fill="#94a3b8"/>
                    <circle cx="55" cy="70" r="5" fill="#f59e0b" stroke="#d97706" stroke-width="2"/>
                </g>
                <text x="35" y="118" font-size="8" fill="#94a3b8" text-anchor="middle" font-weight="bold">{osc_txt}</text>
                <path id="wave-sine-path" d="M 55,70 Q 95,25 135,70 Q 175,115 215,70 Q 255,25 295,70 L 345,70"
                      fill="none" stroke="#06b6d4" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="135" y1="70" x2="135" y2="35" stroke="#ec4899" stroke-width="1.5"/>
                <line id="wave-amp-arrow" x1="135" y1="70" x2="135" y2="35" stroke="#ec4899" stroke-width="1.5"/>
                <text x="142" y="55" font-size="8" fill="#ec4899" font-weight="bold">A</text>
                <line id="wave-lambda-bracket" x1="95" y1="20" x2="255" y2="20" stroke="#f59e0b" stroke-width="1.5"/>
                <polygon points="95,17 95,23 90,20" fill="#f59e0b"/>
                <polygon points="255,17 255,23 260,20" fill="#f59e0b"/>
                <text id="wave-lambda-val" x="175" y="16" font-size="9" fill="#f59e0b" text-anchor="middle" font-weight="bold">λ = 160 m</text>
                <g transform="translate(255, 25)">
                    <rect x="0" y="0" width="90" height="42" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                    <text x="45" y="15" font-size="8" fill="#64748b" text-anchor="middle" font-weight="bold">{speed_txt}</text>
                    <text id="wave-speed-val" x="45" y="28" font-size="11" fill="#0891b2" text-anchor="middle" font-weight="800">0.0 m/s</text>
                    <text id="wave-freq-val" x="45" y="38" font-size="8" fill="#64748b" text-anchor="middle">f = 2.0 Hz</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "dna_pcr":
        thermal_txt = "الدورة الحرارية" if is_ar else "Thermal Cycle"
        amplif_txt = "التضاعف الجيني" if is_ar else "Amplification"
        copies_txt = "عدد النسخ" if is_ar else "Copies"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="DNA PCR Amplification Simulation">
                <rect x="15" y="10" width="330" height="120" rx="10" fill="#0f172a" stroke="#1e293b" stroke-width="2"/>
                <g id="dna-strand-top" style="transition: transform 0.2s ease-out;">
                    <path d="M 60,50 Q 85,38 110,50 Q 135,62 160,50 Q 185,38 210,50 Q 235,62 250,50"
                          fill="none" stroke="#ec4899" stroke-width="3.5" stroke-linecap="round"/>
                    <line x1="85" y1="42" x2="85" y2="58" stroke="#10b981" stroke-width="2"/>
                    <line x1="135" y1="58" x2="135" y2="74" stroke="#f59e0b" stroke-width="2"/>
                    <line x1="185" y1="42" x2="185" y2="58" stroke="#3b82f6" stroke-width="2"/>
                    <line x1="235" y1="58" x2="235" y2="74" stroke="#a855f7" stroke-width="2"/>
                </g>
                <g id="dna-strand-bottom" style="transition: transform 0.2s ease-out;">
                    <path d="M 60,82 Q 85,94 110,82 Q 135,70 160,82 Q 185,94 210,82 Q 235,70 250,82"
                          fill="none" stroke="#06b6d4" stroke-width="3.5" stroke-linecap="round"/>
                </g>
                <g id="taq-enzyme" transform="translate(145, 62)" style="transition: transform 0.25s ease-out;">
                    <rect x="-10" y="-8" width="20" height="16" rx="4" fill="#8b5cf6" opacity="0.85"/>
                    <text x="0" y="3" font-size="7" fill="#ffffff" text-anchor="middle" font-weight="bold">Taq</text>
                </g>
                <g transform="translate(22, 20)">
                    <rect x="0" y="0" width="70" height="52" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>
                    <text x="35" y="15" font-size="7" fill="#94a3b8" text-anchor="middle" font-weight="bold">{thermal_txt}</text>
                    <text id="pcr-cycle-val" x="35" y="30" font-size="11" fill="#ec4899" text-anchor="middle" font-weight="800">n = 1</text>
                    <text id="pcr-temp-text" x="35" y="44" font-size="8" fill="#f59e0b" text-anchor="middle">72°C</text>
                </g>
                <text id="pcr-stage-badge" x="155" y="24" font-size="9" fill="#10b981" text-anchor="middle" font-weight="bold">Extension (72°C)</text>
                <g transform="translate(255, 20)">
                    <rect x="0" y="0" width="80" height="58" rx="6" fill="#1e293b" stroke="#334155" stroke-width="1"/>
                    <text x="40" y="15" font-size="7" fill="#94a3b8" text-anchor="middle" font-weight="bold">{amplif_txt}</text>
                    <text id="pcr-copies-val" x="40" y="32" font-size="10" fill="#10b981" text-anchor="middle" font-weight="800">2</text>
                    <text x="40" y="44" font-size="7" fill="#64748b" text-anchor="middle">{copies_txt}</text>
                    <rect x="8" y="48" width="64" height="4" rx="2" fill="#334155"/>
                    <rect id="pcr-amplification-bar" x="8" y="48" width="10" height="4" rx="2" fill="#10b981" style="transition: width 0.2s;"/>
                </g>
            </svg>
        </div>"""

    elif archetype == "ph_titration":
        meter_txt = "مقياس الـ pH" if is_ar else "pH Meter"
        titrant_txt = "الحجم المضاف" if is_ar else "V Titrant"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Acid-Base Titration and pH Simulation">
                <defs>
                    <linearGradient id="ph-spectrum-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#dc2626"/>
                        <stop offset="35%" stop-color="#f59e0b"/>
                        <stop offset="50%" stop-color="#10b981"/>
                        <stop offset="70%" stop-color="#06b6d4"/>
                        <stop offset="100%" stop-color="#7c3aed"/>
                    </linearGradient>
                </defs>
                <line x1="82" y1="8" x2="82" y2="132" stroke="#64748b" stroke-width="3"/>
                <rect x="55" y="128" width="55" height="6" rx="2" fill="#475569"/>
                <rect x="80" y="24" width="22" height="5" rx="1" fill="#94a3b8"/>
                <rect x="100" y="8" width="12" height="62" rx="2" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" opacity="0.4"/>
                <rect id="burette-liquid" x="101" y="15" width="10" height="54" fill="#60a5fa" opacity="0.6"/>
                <line x1="102" y1="25" x2="108" y2="25" stroke="#475569" stroke-width="1"/>
                <line x1="102" y1="40" x2="108" y2="40" stroke="#475569" stroke-width="1"/>
                <line x1="102" y1="55" x2="108" y2="55" stroke="#475569" stroke-width="1"/>
                <polygon points="103,70 109,70 106,78" fill="#475569"/>
                <rect x="98" y="73" width="16" height="3" rx="1" fill="#f59e0b"/>
                <circle id="titrant-drop" cx="106" cy="85" r="2.2" fill="#60a5fa" opacity="0.8"/>
                <path d="M 98,90 L 114,90 L 114,94 L 134,124 Q 136,128 130,128 L 82,128 Q 76,128 78,124 L 98,94 Z"
                      fill="#f8fafc" stroke="#64748b" stroke-width="2" opacity="0.3"/>
                <path id="titration-liquid" d="M 87,112 L 125,112 L 132,124 Q 134,127 129,127 L 83,127 Q 78,127 80,124 Z"
                      fill="#10b981" opacity="0.85" style="transition: fill 0.3s, d 0.2s;"/>
                <path d="M 120,92 L 116,118" stroke="#334155" stroke-width="2.5" stroke-linecap="round"/>
                <circle cx="116" cy="119" r="2.5" fill="#38bdf8"/>
                <path d="M 120,92 Q 150,75 195,50" fill="none" stroke="#64748b" stroke-width="1.5" stroke-dasharray="2,2"/>
                <g transform="translate(192, 14)">
                    <rect x="0" y="0" width="158" height="114" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>
                    <rect x="10" y="8" width="138" height="18" rx="4" fill="#1e293b"/>
                    <text x="79" y="21" font-size="9" fill="#94a3b8" text-anchor="middle" font-weight="bold">{meter_txt}</text>
                    <rect x="10" y="32" width="138" height="42" rx="6" fill="#020617" stroke="#1e293b" stroke-width="1.5"/>
                    <text id="ph-digital-readout" x="79" y="61" font-size="20" fill="#10b981" text-anchor="middle" font-weight="900" font-family="monospace">pH 7.00</text>
                    <text id="ph-state-badge" x="79" y="86" font-size="9" fill="#10b981" text-anchor="middle" font-weight="bold">متعادل (Neutral)</text>
                    <rect id="ph-color-strip" x="12" y="94" width="134" height="6" rx="3" fill="url(#ph-spectrum-grad)"/>
                    <text id="titrant-vol-val" x="79" y="108" font-size="7" fill="#64748b" text-anchor="middle">{titrant_txt}: 25.0 mL</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "cell_division":
        dish_txt = "طبق بتري (مستعمرة)" if is_ar else "Petri Dish Culture"
        fission_txt = "الانشطار الثنائي" if is_ar else "Binary Fission"
        gen_title = "الجيل" if is_ar else "Generation"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Bacterial Binary Fission and Cell Division Simulation">
                <defs>
                    <radialGradient id="agar-grad" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stop-color="#064e3b" stop-opacity="0.8"/>
                        <stop offset="85%" stop-color="#022c22" stop-opacity="0.95"/>
                        <stop offset="100%" stop-color="#0f172a"/>
                    </radialGradient>
                    <filter id="cell-glow" x="-20%" y="-20%" width="140%" height="140%">
                        <feDropShadow dx="0" dy="0" stdDeviation="2" flood-color="#10b981" flood-opacity="0.6"/>
                    </filter>
                </defs>
                <ellipse cx="108" cy="70" rx="94" ry="58" fill="#0f172a" stroke="#475569" stroke-width="3"/>
                <ellipse cx="108" cy="70" rx="86" ry="50" fill="url(#agar-grad)" stroke="#10b981" stroke-width="1.2" stroke-dasharray="3,3"/>
                <path d="M 28,62 A 80,44 0 0,1 188,62" fill="none" stroke="#ffffff" stroke-width="1.5" opacity="0.15"/>
                <text x="108" y="132" font-size="7" fill="#64748b" text-anchor="middle">{dish_txt}</text>
                <g id="colony-cells-group" filter="url(#cell-glow)">
                    <g id="bact-primary" transform="translate(108, 68)">
                        <ellipse id="bact-cell-1" cx="-7" cy="0" rx="9" ry="5.5" fill="#10b981" stroke="#059669" stroke-width="1.2"/>
                        <ellipse id="bact-cell-2" cx="7" cy="0" rx="9" ry="5.5" fill="#10b981" stroke="#059669" stroke-width="1.2"/>
                        <circle id="bact-dna-1" cx="-7" cy="0" r="2" fill="#a7f3d0"/>
                        <circle id="bact-dna-2" cx="7" cy="0" r="2" fill="#a7f3d0"/>
                    </g>
                    <ellipse id="bact-extra-1" cx="75" cy="52" rx="7" ry="4" fill="#34d399" stroke="#059669" stroke-width="1" transform="rotate(-25, 75, 52)"/>
                    <ellipse id="bact-extra-2" cx="145" cy="55" rx="7" ry="4" fill="#34d399" stroke="#059669" stroke-width="1" transform="rotate(35, 145, 55)"/>
                    <ellipse id="bact-extra-3" cx="78" cy="88" rx="6.5" ry="4" fill="#10b981" stroke="#059669" stroke-width="1" transform="rotate(20, 78, 88)"/>
                    <ellipse id="bact-extra-4" cx="140" cy="85" rx="6.5" ry="4" fill="#10b981" stroke="#059669" stroke-width="1" transform="rotate(-30, 140, 85)"/>
                    <ellipse id="bact-extra-5" cx="110" cy="42" rx="6" ry="3.5" fill="#6ee7b7" stroke="#059669" stroke-width="1"/>
                    <ellipse id="bact-extra-6" cx="110" cy="98" rx="6" ry="3.5" fill="#6ee7b7" stroke="#059669" stroke-width="1"/>
                </g>
                <g transform="translate(216, 14)">
                    <rect x="0" y="0" width="134" height="114" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>
                    <rect x="8" y="8" width="118" height="18" rx="4" fill="#1e293b"/>
                    <text x="67" y="21" font-size="9" fill="#94a3b8" text-anchor="middle" font-weight="bold">{fission_txt}</text>
                    <rect x="8" y="32" width="118" height="42" rx="6" fill="#020617" stroke="#1e293b" stroke-width="1"/>
                    <text x="67" y="46" font-size="8" fill="#94a3b8" text-anchor="middle">{gen_title}</text>
                    <text id="division-gen-val" x="67" y="64" font-size="14" fill="#38bdf8" text-anchor="middle" font-weight="900">n = 0</text>
                    <line x1="8" y1="80" x2="126" y2="80" stroke="#334155" stroke-width="1"/>
                    <text id="division-total-cells" x="67" y="93" font-size="11" fill="#10b981" text-anchor="middle" font-weight="800">1 cell</text>
                    <text id="division-phase-badge" x="67" y="106" font-size="8" fill="#f59e0b" text-anchor="middle">Lag Phase</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "enzyme_kinetics":
        kinetics_txt = "حركية الإنزيم (ميكايليس)" if is_ar else "Enzyme Kinetics"
        cleft_txt = "الموقع النشط" if is_ar else "Active Site"
        vel_title = "السرعة" if is_ar else "Velocity"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Michaelis-Menten Enzyme Kinetics Simulation">
                <defs>
                    <radialGradient id="enzyme-body-grad" cx="40%" cy="40%" r="60%">
                        <stop offset="0%" stop-color="#818cf8"/>
                        <stop offset="70%" stop-color="#4f46e5"/>
                        <stop offset="100%" stop-color="#312e81"/>
                    </radialGradient>
                    <filter id="active-site-glow-filter" x="-30%" y="-30%" width="160%" height="160%">
                        <feGaussianBlur stdDeviation="3" result="blur"/>
                        <feComposite in="SourceGraphic" in2="blur" operator="over"/>
                    </filter>
                </defs>
                <g id="enzyme-molecule" transform="translate(10, 10)">
                    <path d="M 40,25 C 70,5 110,12 125,35 C 135,50 120,62 108,65 C 96,68 96,82 108,85 C 122,88 132,100 120,118 C 100,132 50,130 30,110 C 10,90 15,45 40,25 Z"
                          fill="url(#enzyme-body-grad)" stroke="#4338ca" stroke-width="2.5"/>
                    <circle id="active-site-glow" cx="102" cy="75" r="14" fill="#38bdf8" opacity="0.3" filter="url(#active-site-glow-filter)"/>
                    <text x="75" y="78" font-size="7" fill="#e0e7ff" font-weight="bold">{cleft_txt}</text>
                    <g id="substrate-dock" transform="translate(135, 70)" style="transition: transform 0.2s ease-out;">
                        <polygon points="0,-7 12,0 0,7 -4,0" fill="#f59e0b" stroke="#d97706" stroke-width="1.5"/>
                        <circle cx="2" cy="0" r="1.5" fill="#ffffff"/>
                    </g>
                    <g id="substrate-pool">
                        <polygon points="160,25 168,30 160,35 156,30" fill="#f59e0b" opacity="0.75"/>
                        <polygon points="175,50 183,55 175,60 171,55" fill="#f59e0b" opacity="0.6"/>
                        <polygon points="165,100 173,105 165,110 161,105" fill="#f59e0b" opacity="0.7"/>
                        <polygon points="182,85 190,90 182,95 178,90" fill="#f59e0b" opacity="0.5"/>
                    </g>
                </g>
                <g transform="translate(210, 14)">
                    <rect x="0" y="0" width="140" height="114" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>
                    <rect x="8" y="8" width="124" height="18" rx="4" fill="#1e293b"/>
                    <text x="70" y="21" font-size="9" fill="#94a3b8" text-anchor="middle" font-weight="bold">{kinetics_txt}</text>
                    <rect x="8" y="32" width="124" height="42" rx="6" fill="#020617" stroke="#1e293b" stroke-width="1"/>
                    <text x="70" y="45" font-size="7" fill="#94a3b8" text-anchor="middle">{vel_title}</text>
                    <text id="enzyme-v-val" x="70" y="63" font-size="13" fill="#38bdf8" text-anchor="middle" font-weight="900">v = 0.0</text>
                    <rect x="10" y="78" width="120" height="6" rx="3" fill="#1e293b"/>
                    <rect id="enzyme-sat-bar" x="10" y="78" width="20" height="6" rx="3" fill="#10b981" style="transition: width 0.2s;"/>
                    <text id="enzyme-s-val" x="70" y="94" font-size="8" fill="#f59e0b" text-anchor="middle" font-weight="bold">[S] = 10 mM</text>
                    <text id="enzyme-state-badge" x="70" y="106" font-size="7" fill="#10b981" text-anchor="middle">1st Order ([S] &lt; Km)</text>
                </g>
            </svg>
        </div>"""

    elif archetype == "thermo_calorimeter":
        calor_txt = "المسعر الحراري" if is_ar else "Calorimeter"
        heat_title = "كمية الحرارة (q)" if is_ar else "Heat Exchange (q)"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Thermochemistry Calorimeter Simulation">
                <defs>
                    <linearGradient id="calor-fluid-grad" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop id="calor-grad-stop1" offset="0%" stop-color="#38bdf8"/>
                        <stop id="calor-grad-stop2" offset="100%" stop-color="#0284c7"/>
                    </linearGradient>
                </defs>
                <rect x="75" y="20" width="115" height="110" rx="8" fill="#1e293b" stroke="#475569" stroke-width="2.5"/>
                <rect x="80" y="25" width="105" height="100" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>
                <rect id="calorimeter-fluid" x="84" y="60" width="97" height="60" rx="4" fill="url(#calor-fluid-grad)" opacity="0.85" style="transition: fill 0.3s;"/>
                <rect x="68" y="16" width="129" height="10" rx="2" fill="#334155" stroke="#475569" stroke-width="1.5"/>
                <g id="calorimeter-stirrer-group">
                    <line x1="102" y1="8" x2="102" y2="105" stroke="#94a3b8" stroke-width="2"/>
                    <line x1="94" y1="105" x2="110" y2="105" stroke="#94a3b8" stroke-width="2.5"/>
                    <circle cx="102" cy="8" r="4" fill="#64748b"/>
                </g>
                <g id="calorimeter-thermometer-group">
                    <rect x="140" y="8" width="8" height="108" rx="4" fill="#ffffff" stroke="#94a3b8" stroke-width="1.2" opacity="0.6"/>
                    <rect id="calorimeter-mercury" x="142" y="70" width="4" height="42" rx="2" fill="#ef4444" style="transition: height 0.2s, y 0.2s;"/>
                    <circle cx="144" cy="114" r="5" fill="#ef4444"/>
                    <line x1="140" y1="30" x2="143" y2="30" stroke="#475569" stroke-width="1"/>
                    <line x1="140" y1="50" x2="143" y2="50" stroke="#475569" stroke-width="1"/>
                    <line x1="140" y1="70" x2="143" y2="70" stroke="#475569" stroke-width="1"/>
                </g>
                <g transform="translate(205, 14)">
                    <rect x="0" y="0" width="145" height="114" rx="8" fill="#0f172a" stroke="#334155" stroke-width="1.5"/>
                    <rect x="8" y="8" width="129" height="18" rx="4" fill="#1e293b"/>
                    <text x="72" y="21" font-size="9" fill="#94a3b8" text-anchor="middle" font-weight="bold">{calor_txt}</text>
                    <rect x="8" y="32" width="129" height="42" rx="6" fill="#020617" stroke="#1e293b" stroke-width="1"/>
                    <text x="72" y="45" font-size="7" fill="#94a3b8" text-anchor="middle">{heat_title}</text>
                    <text id="calorimeter-q-val" x="72" y="63" font-size="14" fill="#f59e0b" text-anchor="middle" font-weight="900">q = 0.0 J</text>
                    <line x1="8" y1="80" x2="137" y2="80" stroke="#334155" stroke-width="1"/>
                    <text id="calorimeter-temp-val" x="72" y="93" font-size="9" fill="#38bdf8" text-anchor="middle" font-weight="bold">ΔT = 0.0 °C</text>
                    <text id="calorimeter-state-badge" x="72" y="106" font-size="8" fill="#10b981" text-anchor="middle">طارد للحرارة (Exothermic)</text>
                </g>
            </svg>
        </div>"""

    else:
        min_txt = "الأدنى" if is_ar else "Min"
        mid_txt = "الوسط" if is_ar else "Mid"
        max_txt = "الأقصى" if is_ar else "Max"
        return f"""
        <div class="visual-display">
            <svg id="visual-svg" width="360" height="140" viewBox="0 0 360 140" aria-label="Scientific Gauge Meter">
                <path d="M 80,105 A 100,100 0 0,1 280,105" fill="none" stroke="#e2e8f0" stroke-width="14" stroke-linecap="round"/>
                <line x1="80" y1="105" x2="92" y2="105" stroke="#64748b" stroke-width="2"/>
                <text x="70" y="118" font-size="9" fill="#64748b" font-weight="bold">{min_txt}</text>
                <line x1="180" y1="5" x2="180" y2="17" stroke="#64748b" stroke-width="2"/>
                <text x="180" y="27" font-size="9" fill="#64748b" font-weight="bold" text-anchor="middle">{mid_txt}</text>
                <line x1="280" y1="105" x2="268" y2="105" stroke="#64748b" stroke-width="2"/>
                <text x="290" y="118" font-size="9" fill="#64748b" font-weight="bold">{max_txt}</text>
                <g transform="translate(180, 105)">
                    <line id="gauge-needle" x1="0" y1="0" x2="0" y2="-85" stroke="#ef4444" stroke-width="3" stroke-linecap="round" style="transition: transform 0.2s ease-out; transform: rotate(0deg);"/>
                    <circle cx="0" cy="0" r="7" fill="#1e293b"/>
                    <circle cx="0" cy="0" r="3" fill="#ffffff"/>
                </g>
                <rect x="140" y="114" width="80" height="22" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>
                <text id="gauge-digital-val" x="180" y="129" font-size="11" font-weight="800" fill="#4f46e5" text-anchor="middle">0.00</text>
            </svg>
        </div>"""


def _get_archetype_js(archetype: str, is_ar: bool = False) -> str:
    """Returns the dedicated JS animation logic for the selected archetype."""
    is_ar_js = "true" if is_ar else "false"

    if archetype == "spring":
        return """
        function generateSpringPath(startX, startY, length, numCoils) {
            numCoils = numCoils || 5;
            let d = "M " + startX + "," + startY;
            const coilLength = Math.max(10, length - 16);
            const stepY = coilLength / (numCoils * 2);
            d += " L " + startX + "," + (startY + 8);
            for (let i = 0; i < numCoils; i++) {
                const y1 = startY + 8 + (i * 2 + 0.5) * stepY;
                const y2 = startY + 8 + (i * 2 + 1.5) * stepY;
                d += " Q " + (startX - 18) + "," + y1.toFixed(1) + " " + startX + "," + (startY + 8 + (i * 2 + 1) * stepY).toFixed(1);
                d += " Q " + (startX + 18) + "," + y2.toFixed(1) + " " + startX + "," + (startY + 8 + (i * 2 + 2) * stepY).toFixed(1);
            }
            d += " L " + startX + "," + (startY + length);
            return d;
        }

        function animateArchetype(result, values, pct) {
            const xVal = values['x'] !== undefined ? values['x'] : (values['Δx'] || values['d'] || (result / (values['k'] || 50)));
            const extPx = Math.max(5, Math.min(55, xVal * 60));
            const totalLength = 46 + extPx;
            const coilPath = document.getElementById('spring-coil-path');
            if (coilPath) coilPath.setAttribute('d', generateSpringPath(180, 16, totalLength, 5));
            const massGroup = document.getElementById('spring-mass-group');
            if (massGroup) massGroup.setAttribute('transform', 'translate(0, ' + extPx.toFixed(1) + ')');
            const massLabel = document.getElementById('mass-label');
            if (massLabel) massLabel.textContent = 'F = ' + formatNum(result) + ' N';
        }
        """
    elif archetype == "circuit":
        return """
        function animateArchetype(result, values, pct) {
            const iVal = values['I'] !== undefined ? values['I'] : (result / (values['R'] || 10));
            const bulbGlow = document.getElementById('bulb-glow');
            if (bulbGlow) {
                const glowOp = Math.max(0.05, Math.min(0.95, iVal / 5.0));
                bulbGlow.style.opacity = glowOp.toFixed(2);
                bulbGlow.setAttribute('r', (14 + glowOp * 16).toFixed(0));
            }
            const currLabel = document.getElementById('current-label');
            if (currLabel) currLabel.textContent = formatNum(iVal) + ' A';
            const vLabel = document.getElementById('battery-label');
            if (vLabel && values['V'] !== undefined) vLabel.textContent = formatNum(values['V']) + ' V';
            const rLabel = document.getElementById('resistor-label');
            if (rLabel && values['R'] !== undefined) rLabel.textContent = 'R = ' + formatNum(values['R']) + ' Ω';
        }
        """
    elif archetype == "beaker":
        return f"""
        function animateArchetype(result, values, pct) {{
            const liquid = document.getElementById('beaker-liquid');
            const concEl = document.getElementById('beaker-conc-val');
            const stateBadge = document.getElementById('beaker-state-badge');
            const volEl = document.getElementById('beaker-vol-val');

            const vVal = values['V'] !== undefined ? values['V'] : (values['v'] || values['vol'] || values['V1'] || 150);
            const concVal = values['M'] !== undefined ? values['M'] : (values['C'] || values['c'] || values['molarity'] || result);

            if (liquid) {{
                const liquidH = Math.max(16, Math.min(85, 20 + Math.min(100, vVal) * 0.6));
                liquid.setAttribute('height', liquidH.toFixed(1));
                liquid.setAttribute('y', (128 - liquidH).toFixed(1));
                const opacityNorm = Math.max(0.3, Math.min(0.95, 0.3 + (pct / 100) * 0.65));
                liquid.setAttribute('fill-opacity', opacityNorm.toFixed(2));
            }}

            if (concEl) {{
                concEl.textContent = formatNum(concVal) + ' M';
            }}

            if (volEl) {{
                volEl.textContent = 'V = ' + formatNum(vVal) + ' mL';
            }}

            if (stateBadge) {{
                let stateTxt = '';
                let stateColor = '#10b981';
                if (pct < 30) {{
                    stateTxt = {is_ar_js} ? 'مخفف (Dilute)' : 'Dilute';
                    stateColor = '#38bdf8';
                }} else if (pct <= 70) {{
                    stateTxt = {is_ar_js} ? 'معياري (Standard)' : 'Standard';
                    stateColor = '#10b981';
                }} else {{
                    stateTxt = {is_ar_js} ? 'مركز (Concentrated)' : 'Concentrated';
                    stateColor = '#f59e0b';
                }}
                stateBadge.textContent = stateTxt;
                stateBadge.setAttribute('fill', stateColor);
            }}

            const particles = document.getElementById('beaker-solute-particles');
            if (particles) {{
                particles.style.opacity = Math.max(0.2, Math.min(1.0, (pct / 100) * 1.2)).toFixed(2);
            }}
        }}
        """
    elif archetype == "piston":
        return """
        function animateArchetype(result, values, pct) {
            let volRatio = 0.5;
            if (values['V'] !== undefined) {
                const vMeta = (typeof varsMeta !== 'undefined' && varsMeta) ? varsMeta.find(v => v.symbol === 'V') : null;
                const vMin = vMeta ? vMeta.min_val : 1;
                const vMax = vMeta ? vMeta.max_val : 100;
                volRatio = Math.max(0, Math.min(1, (values['V'] - vMin) / Math.max(vMax - vMin, 1e-4)));
            } else if (values['v'] !== undefined) {
                const vMeta = (typeof varsMeta !== 'undefined' && varsMeta) ? varsMeta.find(v => v.symbol === 'v') : null;
                const vMin = vMeta ? vMeta.min_val : 1;
                const vMax = vMeta ? vMeta.max_val : 100;
                volRatio = Math.max(0, Math.min(1, (values['v'] - vMin) / Math.max(vMax - vMin, 1e-4)));
            } else {
                volRatio = Math.max(0, Math.min(1, 1 - (pct / 100)));
            }
            const pAssembly = document.getElementById('piston-assembly');
            const pNeedle = document.getElementById('piston-gauge-needle');
            const pText = document.getElementById('piston-pressure-text');
            const dispY = (1 - volRatio) * 54;
            if (pAssembly) pAssembly.setAttribute('transform', 'translate(0, ' + dispY.toFixed(1) + ')');
            const needleAngle = -75 + (Math.max(0, Math.min(100, pct)) / 100) * 150;
            if (pNeedle) pNeedle.setAttribute('transform', 'rotate(' + needleAngle.toFixed(1) + ', 268, 55)');
            const unitStr = (typeof resultUnit !== 'undefined' && resultUnit) ? resultUnit : 'atm';
            if (pText) pText.textContent = 'P = ' + formatNum(result) + ' ' + unitStr;
        }
        """
    elif archetype in ("cell_osmosis", "cell"):
        return f"""
        function animateArchetype(result, values, pct) {{
            const membrane = document.getElementById('cell-membrane');
            const stateLabel = document.getElementById('cell-state-label');
            const normPct = Math.max(0, Math.min(100, pct));
            const rx = Math.min(58, Math.max(30, 58 - (normPct / 100) * 26));
            const ry = Math.min(42, Math.max(20, 42 - (normPct / 100) * 19));
            if (membrane) {{
                membrane.setAttribute('rx', rx.toFixed(1));
                membrane.setAttribute('ry', ry.toFixed(1));
            }}
            if (stateLabel) {{
                if (normPct > 65) {{
                    stateLabel.textContent = {is_ar_js} ? 'محلول مرتفع (Hypertonic)' : 'Hypertonic';
                    stateLabel.setAttribute('fill', '#ef4444');
                }} else if (normPct < 35) {{
                    stateLabel.textContent = {is_ar_js} ? 'محلول منخفض (Hypotonic)' : 'Hypotonic';
                    stateLabel.setAttribute('fill', '#0284c7');
                }} else {{
                    stateLabel.textContent = {is_ar_js} ? 'محلول متعادل (Isotonic)' : 'Isotonic';
                    stateLabel.setAttribute('fill', '#9333ea');
                }}
            }}
        }}
        """
    elif archetype in ("lever_torque", "lever"):
        return """
        function animateArchetype(result, values, pct) {
            const beam = document.getElementById('lever-beam-group');
            if (beam) {
                const angle = Math.max(-16, Math.min(16, (pct - 50) * 0.32));
                beam.setAttribute('transform', 'rotate(' + angle.toFixed(1) + ', 180, 56)');
            }
        }
        """
    elif archetype == "gauge":
        return """
        function animateArchetype(result, values, pct) {
            const needle = document.getElementById('gauge-needle');
            const digi = document.getElementById('gauge-digital-val');
            const angle = Math.max(-90, Math.min(90, (pct - 50) * 1.8));
            if (needle) needle.style.transform = 'rotate(' + angle.toFixed(1) + 'deg)';
            if (digi) digi.textContent = formatNum(result);
        }
        """
    elif archetype == "spectrophotometer":
        return f"""
        function animateArchetype(result, values, pct) {{
            const cVal = values['c'] !== undefined ? values['c'] : (values['C'] !== undefined ? values['C'] : (values['conc'] || 0.5));
            const absVal = values['A'] !== undefined ? values['A'] : result;
            const A = Math.max(0, absVal);
            const T = Math.max(0, Math.min(100, Math.pow(10, -A) * 100));

            const liquid = document.getElementById('cuvette-liquid');
            if (liquid) {{
                const concNorm = Math.max(0.12, Math.min(0.95, (cVal * 0.25) || (A * 0.4) || (pct / 100)));
                liquid.style.opacity = concNorm.toFixed(2);
            }}

            const beamTrans = document.getElementById('beam-transmitted');
            if (beamTrans) {{
                const tNorm = T / 100;
                beamTrans.style.opacity = Math.max(0.06, tNorm).toFixed(2);
                beamTrans.setAttribute('stroke-width', Math.max(1.5, tNorm * 8).toFixed(1));
            }}

            const absEl = document.getElementById('spectro-abs-val');
            if (absEl) absEl.textContent = formatNum(A);

            const transEl = document.getElementById('spectro-trans-val');
            if (transEl) transEl.textContent = formatNum(T) + '%';

            const statusEl = document.getElementById('spectro-status');
            if (statusEl) {{
                if ({is_ar_js}) {{
                    statusEl.textContent = A < 0.2 ? 'نفاذية مرتفعة' : (A > 1.8 ? 'تشبع ضوئي تام' : 'امتصاص قياسي منتظم');
                }} else {{
                    statusEl.textContent = A < 0.2 ? 'High Transmittance' : (A > 1.8 ? 'Optical Saturation' : 'Standard Absorbance');
                }}
            }}
        }}
        """

    elif archetype == "optics_bench":
        return f"""
        function animateArchetype(result, values, pct) {{
            const doVal = values['d_o'] !== undefined ? values['d_o'] : (values['do'] !== undefined ? values['do'] : (values['d'] || 60));
            const fVal = values['f'] !== undefined ? values['f'] : 30;
            const ho = values['h_o'] !== undefined ? values['h_o'] : (values['h'] || 35);

            let di = 0;
            if (Math.abs(doVal - fVal) > 0.01) {{
                di = (fVal * doVal) / (doVal - fVal);
            }} else {{
                di = 999;
            }}

            const m = doVal !== 0 ? -di / doVal : 0;
            const hi = m * ho;

            const objX = Math.max(35, Math.min(160, 180 - doVal * 1.8));
            const imgX = Math.max(200, Math.min(335, 180 + di * 1.8));

            const objGroup = document.getElementById('optics-object-group');
            if (objGroup) {{
                objGroup.setAttribute('transform', 'translate(' + objX.toFixed(1) + ', 70)');
            }}

            const imgGroup = document.getElementById('optics-image-group');
            if (imgGroup) {{
                imgGroup.setAttribute('transform', 'translate(' + imgX.toFixed(1) + ', 70) scale(1, ' + (m < 0 ? '1' : '-1') + ')');
            }}

            const rayPar = document.getElementById('ray-parallel');
            const rayCen = document.getElementById('ray-central');
            const objTipY = 70 - ho;
            const imgTipY = 70 + hi;

            if (rayPar) {{
                rayPar.setAttribute('d', 'M ' + objX.toFixed(1) + ',' + objTipY + ' L 180,' + objTipY + ' L ' + imgX.toFixed(1) + ',' + imgTipY.toFixed(1));
            }}
            if (rayCen) {{
                rayCen.setAttribute('d', 'M ' + objX.toFixed(1) + ',' + objTipY + ' L 180,70 L ' + imgX.toFixed(1) + ',' + imgTipY.toFixed(1));
            }}

            const badge = document.getElementById('optics-nature-badge');
            if (badge) {{
                if (di > 0) {{
                    badge.textContent = {is_ar_js} ? 'حقيقية ومقلوبة (m=' + formatNum(m) + ')' : 'Real / Inverted (m=' + formatNum(m) + ')';
                    badge.setAttribute('fill', '#4f46e5');
                }} else {{
                    badge.textContent = {is_ar_js} ? 'تقديرية ومعتدلة (m=' + formatNum(m) + ')' : 'Virtual / Upright (m=' + formatNum(m) + ')';
                    badge.setAttribute('fill', '#f59e0b');
                }}
            }}
        }}
        """

    elif archetype == "refraction":
        return f"""
        function animateArchetype(result, values, pct) {{
            const n1 = values['n1'] !== undefined ? values['n1'] : (values['n_1'] || 1.0);
            const n2 = values['n2'] !== undefined ? values['n2'] : (values['n_2'] || 1.5);
            const theta1Deg = values['θ1'] !== undefined ? values['θ1'] : (values['theta1'] !== undefined ? values['theta1'] : (values['θ'] || (pct * 0.8)));
            const theta1Rad = (theta1Deg * Math.PI) / 180;

            const sinTheta2 = (n1 / n2) * Math.sin(theta1Rad);
            const isTIR = sinTheta2 > 1.0;

            let theta2Deg = 0;
            if (!isTIR) {{
                theta2Deg = (Math.asin(Math.max(-1, Math.min(1, sinTheta2))) * 180) / Math.PI;
            }}

            const L = 60;
            const incX = 180 - L * Math.sin(theta1Rad);
            const incY = 70 - L * Math.cos(theta1Rad);
            const incRay = document.getElementById('incident-ray');
            if (incRay) {{
                incRay.setAttribute('x1', incX.toFixed(1));
                incRay.setAttribute('y1', incY.toFixed(1));
            }}

            const refRay = document.getElementById('refracted-ray');
            const reflRay = document.getElementById('reflected-ray');
            const tirBadge = document.getElementById('tir-badge-group');

            if (isTIR) {{
                if (refRay) refRay.style.opacity = '0';
                if (reflRay) reflRay.style.opacity = '0.9';
                if (tirBadge) tirBadge.style.display = 'block';
            }} else {{
                if (refRay) {{
                    refRay.style.opacity = '1';
                    const theta2Rad = (theta2Deg * Math.PI) / 180;
                    const refX = 180 + L * Math.sin(theta2Rad);
                    const refY = 70 + L * Math.cos(theta2Rad);
                    refRay.setAttribute('x2', refX.toFixed(1));
                    refRay.setAttribute('y2', refY.toFixed(1));
                }}
                if (reflRay) reflRay.style.opacity = '0.2';
                if (tirBadge) tirBadge.style.display = 'none';
            }}

            const t1Text = document.getElementById('angle-theta1-text');
            if (t1Text) t1Text.textContent = formatNum(theta1Deg) + '°';

            const t2Text = document.getElementById('angle-theta2-text');
            if (t2Text) t2Text.textContent = isTIR ? 'TIR' : formatNum(theta2Deg) + '°';
        }}
        """

    elif archetype == "kinematics_block":
        return f"""
        function animateArchetype(result, values, pct) {{
            const fVal = values['F'] !== undefined ? values['F'] : (values['F_app'] || (result > 0 ? result : 15));
            const mVal = values['m'] !== undefined ? values['m'] : (values['M'] || 5);
            const muVal = values['μ'] !== undefined ? values['μ'] : (values['mu'] || 0.2);
            const fricVal = muVal * mVal * 9.8;
            const aVal = values['a'] !== undefined ? values['a'] : Math.max(0, (fVal - fricVal) / Math.max(0.1, mVal));

            const dispX = 40 + (pct / 100) * 160;
            const blockGroup = document.getElementById('kinematics-block-group');
            if (blockGroup) {{
                blockGroup.setAttribute('transform', 'translate(' + dispX.toFixed(1) + ', 62)');
            }}

            const vForce = document.getElementById('vector-force');
            if (vForce) {{
                const arrowLen = Math.max(15, Math.min(65, fVal * 2.5));
                vForce.setAttribute('x2', (65 + arrowLen).toFixed(1));
            }}

            const vFric = document.getElementById('vector-friction');
            if (vFric) {{
                const arrowLen = Math.max(10, Math.min(45, fricVal * 2.5));
                vFric.setAttribute('x2', (-arrowLen).toFixed(1));
            }}

            const fEl = document.getElementById('force-val');
            if (fEl) fEl.textContent = formatNum(fVal) + ' N';

            const fricEl = document.getElementById('friction-val');
            if (fricEl) fricEl.textContent = formatNum(fricVal) + ' N';

            const accEl = document.getElementById('accel-val');
            if (accEl) accEl.textContent = 'a = ' + formatNum(aVal) + ' m/s²';

            const mLabel = document.getElementById('block-mass-label');
            if (mLabel) mLabel.textContent = formatNum(mVal) + ' kg';
        }}
        """

    elif archetype == "pendulum":
        return f"""
        function animateArchetype(result, values, pct) {{
            const LVal = values['L'] !== undefined ? values['L'] : (values['l'] || 1.0);
            const gVal = values['g'] !== undefined ? values['g'] : 9.8;
            const period = 2 * Math.PI * Math.sqrt(Math.max(0.01, LVal / gVal));

            const thetaDeg = values['θ'] !== undefined ? values['θ'] : (values['theta'] !== undefined ? values['theta'] : ((pct - 50) * 0.8));
            const thetaClamped = Math.max(-45, Math.min(45, thetaDeg));

            const armGroup = document.getElementById('pendulum-arm-group');
            if (armGroup) {{
                armGroup.setAttribute('transform', 'rotate(' + thetaClamped.toFixed(1) + ', 180, 14)');
            }}

            const thetaRad = (Math.abs(thetaClamped) * Math.PI) / 180;
            const peRatio = Math.max(0, Math.min(1, (1 - Math.cos(thetaRad)) / (1 - Math.cos(45 * Math.PI / 180))));
            const keRatio = 1.0 - peRatio;

            const keFill = document.getElementById('bar-ke-fill');
            const peFill = document.getElementById('bar-pe-fill');

            if (keFill) {{
                const keH = Math.max(4, Math.round(keRatio * 46));
                keFill.setAttribute('height', keH.toString());
                keFill.setAttribute('y', (72 - keH).toString());
            }}
            if (peFill) {{
                const peH = Math.max(4, Math.round(peRatio * 46));
                peFill.setAttribute('height', peH.toString());
                peFill.setAttribute('y', (72 - peH).toString());
            }}

            const pVal = document.getElementById('pendulum-period-val');
            if (pVal) pVal.textContent = formatNum(period) + ' s';

            const aVal = document.getElementById('pendulum-angle-val');
            if (aVal) aVal.textContent = 'θ = ' + formatNum(thetaClamped) + '°';
        }}
        """

    elif archetype == "projectile":
        return f"""
        function animateArchetype(result, values, pct) {{
            const v0 = values['v0'] !== undefined ? values['v0'] : (values['v'] !== undefined ? values['v'] : (values['v_0'] !== undefined ? values['v_0'] : (values['velocity'] !== undefined ? values['velocity'] : (values['u'] !== undefined ? values['u'] : 25))));
            const thetaDeg = values['θ'] !== undefined ? values['θ'] : (values['theta'] !== undefined ? values['theta'] : (values['angle'] !== undefined ? values['angle'] : (values['Angle'] !== undefined ? values['Angle'] : (values['α'] !== undefined ? values['α'] : (pct * 0.85 + 5)))));
            const g = values['g'] !== undefined ? values['g'] : ((typeof constants !== 'undefined' && constants && constants['g']) ? constants['g'] : 9.8);
            const thetaClamped = Math.max(5, Math.min(85, thetaDeg));
            const rad = (thetaClamped * Math.PI) / 180;

            const barrel = document.getElementById('cannon-barrel');
            if (barrel) {{
                barrel.setAttribute('transform', 'rotate(' + (-thetaClamped).toFixed(1) + ', 35, 115)');
                barrel.style.transform = 'rotate(' + (-thetaClamped).toFixed(1) + 'deg)';
            }}

            const R = (Math.pow(v0, 2) * Math.sin(2 * rad)) / g;
            const H = (Math.pow(v0, 2) * Math.pow(Math.sin(rad), 2)) / (2 * g);
            const T = (2 * v0 * Math.sin(rad)) / g;

            const scaleX = 260 / Math.max(40, R * 1.15);
            const scaleY = 80 / Math.max(10, H * 1.25);
            const scale = Math.min(scaleX, scaleY);

            const screenR = Math.min(280, Math.max(25, R * scale));
            const screenH = Math.min(90, Math.max(10, H * scale));

            const peakX = 35 + screenR / 2;
            const peakY = 115 - screenH;
            const endX = 35 + screenR;

            const traj = document.getElementById('trajectory-path');
            if (traj) {{
                const ctrlY = 115 - (2 * screenH);
                traj.setAttribute('d', 'M 35,115 Q ' + peakX.toFixed(1) + ',' + ctrlY.toFixed(1) + ' ' + endX.toFixed(1) + ',115');
            }}

            const pBall = document.getElementById('projectile-ball');
            if (pBall) {{
                pBall.setAttribute('cx', peakX.toFixed(1));
                pBall.setAttribute('cy', peakY.toFixed(1));
            }}

            const mPeak = document.getElementById('marker-peak');
            if (mPeak) {{
                mPeak.setAttribute('transform', 'translate(' + peakX.toFixed(1) + ',' + peakY.toFixed(1) + ')');
            }}

            const mRange = document.getElementById('marker-range');
            if (mRange) {{
                mRange.setAttribute('transform', 'translate(' + endX.toFixed(1) + ', 115)');
            }}

            const rEl = document.getElementById('telemetry-range');
            if (rEl) rEl.textContent = formatNum(R) + ' m';
            const hEl = document.getElementById('telemetry-hmax');
            if (hEl) hEl.textContent = formatNum(H) + ' m';
            const tEl = document.getElementById('telemetry-time');
            if (tEl) tEl.textContent = formatNum(T) + ' s';
            const aEl = document.getElementById('telemetry-angle');
            if (aEl) aEl.textContent = 'θ = ' + formatNum(thetaClamped) + '°';
        }}
        """

    elif archetype == "gravity_orbit":
        return f"""
        function animateArchetype(result, values, pct) {{
            const rVal = values['r'] !== undefined ? values['r'] : (values['R'] || (pct * 0.8 + 20));
            const mCore = values['M'] !== undefined ? values['M'] : (values['m1'] || 5.972e24);
            const mSat = values['m'] !== undefined ? values['m'] : (values['m2'] || 1000);
            const G_PHYSICAL = 6.6743e-11;
            const Fg = (G_PHYSICAL * mCore * mSat) / Math.max(1.0, Math.pow(rVal, 2));
            const vOrb = Math.sqrt((G_PHYSICAL * mCore) / Math.max(rVal, 1)) / 1000;

            const rx = Math.max(35, Math.min(135, 35 + (pct / 100) * 95));
            const ry = rx * 0.42;

            const orbitPath = document.getElementById('orbit-path');
            if (orbitPath) {{
                orbitPath.setAttribute('rx', rx.toFixed(1));
                orbitPath.setAttribute('ry', ry.toFixed(1));
            }}

            const angleRad = ((pct * 3.6) * Math.PI) / 180;
            const satX = 170 + rx * Math.cos(angleRad);
            const satY = 70 + ry * Math.sin(angleRad);

            const satGroup = document.getElementById('orbiting-body');
            if (satGroup) {{
                satGroup.setAttribute('transform', 'translate(' + satX.toFixed(1) + ',' + satY.toFixed(1) + ')');
            }}

            const vGrav = document.getElementById('vector-gravity');
            if (vGrav) {{
                const dx = 170 - satX;
                const dy = 70 - satY;
                const dist = Math.sqrt(dx * dx + dy * dy) || 1;
                const fLen = Math.max(10, Math.min(30, 10 + (pct / 100) * 18));
                vGrav.setAttribute('x1', '0');
                vGrav.setAttribute('y1', '0');
                vGrav.setAttribute('x2', ((dx / dist) * fLen).toFixed(1));
                vGrav.setAttribute('y2', ((dy / dist) * fLen).toFixed(1));
            }}

            const vVel = document.getElementById('vector-velocity');
            if (vVel) {{
                const vx = -rx * Math.sin(angleRad);
                const vy = ry * Math.cos(angleRad);
                const vDist = Math.sqrt(vx * vx + vy * vy) || 1;
                const vLen = Math.max(12, Math.min(32, 12 + ((100 - pct) / 100) * 18));
                vVel.setAttribute('x1', '0');
                vVel.setAttribute('y1', '0');
                vVel.setAttribute('x2', ((vx / vDist) * vLen).toFixed(1));
                vVel.setAttribute('y2', ((vy / vDist) * vLen).toFixed(1));
            }}

            const rEl = document.getElementById('orbit-radius-val');
            if (rEl) rEl.textContent = formatNum(rVal) + ' m';
            const sEl = document.getElementById('orbit-speed-val');
            if (sEl) sEl.textContent = formatNum(vOrb) + ' km/s';
            const fEl = document.getElementById('orbit-force-val');
            if (fEl) fEl.textContent = ({is_ar_js} ? 'قوة الجاذبية: ' : 'Gravity: ') + formatNum(result || Fg) + ' N';
        }}
        """

    elif archetype == "wave_oscillator":
        return f"""
        function animateArchetype(result, values, pct) {{
            const resSym = (typeof resultSymbol !== 'undefined' && resultSymbol) ? resultSymbol.toLowerCase() : '';
            const isCalcLambda = resSym === 'λ' || resSym === 'lambda' || resSym === 'l';
            const isCalcSpeed = resSym === 'v' || resSym === 'speed' || resSym === 'c';
            const isCalcFreq = resSym === 'f' || resSym === 'freq';

            const A = values['A'] !== undefined ? values['A'] : (values['a'] || (pct * 0.35 + 10));
            const f = isCalcFreq ? result : (values['f'] !== undefined ? values['f'] : (values['freq'] || 2.0));

            let lambda = 80;
            if (isCalcLambda) {{
                lambda = result;
            }} else if (values['λ'] !== undefined) {{
                lambda = values['λ'];
            }} else if (values['lambda'] !== undefined) {{
                lambda = values['lambda'];
            }} else if (values['L'] !== undefined) {{
                lambda = values['L'];
            }} else if (values['l'] !== undefined) {{
                lambda = values['l'];
            }} else if (values['wavelength'] !== undefined) {{
                lambda = values['wavelength'];
            }} else if (isCalcSpeed && f > 0) {{
                lambda = result / f;
            }} else if (values['v'] !== undefined && f > 0) {{
                lambda = values['v'] / f;
            }}

            const speed = isCalcSpeed ? result : (values['v'] !== undefined ? values['v'] : (f * lambda));

            const ampPx = Math.max(5, Math.min(42, A * 1.2));
            const lambdaPx = Math.max(35, Math.min(180, lambda));

            const piston = document.getElementById('oscillator-piston');
            if (piston) {{
                piston.setAttribute('transform', 'translate(0, ' + (-ampPx).toFixed(1) + ')');
            }}

            let d = 'M 55,' + (70 - ampPx).toFixed(1);
            const startX = 55;
            const endX = 345;
            const step = 4;
            for (let x = startX + step; x <= endX; x += step) {{
                const relX = x - startX;
                const y = 70 - ampPx * Math.cos((2 * Math.PI * relX) / lambdaPx);
                d += ' L ' + x.toFixed(1) + ',' + y.toFixed(1);
            }}

            const wavePath = document.getElementById('wave-sine-path');
            if (wavePath) {{
                wavePath.setAttribute('d', d);
            }}

            const ampArrow = document.getElementById('wave-amp-arrow');
            if (ampArrow) {{
                ampArrow.setAttribute('y2', (70 - ampPx).toFixed(1));
            }}

            const lambdaBracket = document.getElementById('wave-lambda-bracket');
            if (lambdaBracket) {{
                lambdaBracket.setAttribute('x2', Math.min(340, 95 + lambdaPx).toFixed(1));
            }}

            const spEl = document.getElementById('wave-speed-val');
            if (spEl) spEl.textContent = formatNum(speed) + ' m/s';
            const frEl = document.getElementById('wave-freq-val');
            if (frEl) frEl.textContent = 'f = ' + formatNum(f) + ' Hz';
            const lamEl = document.getElementById('wave-lambda-val');
            if (lamEl) lamEl.textContent = 'λ = ' + formatNum(lambda) + ' m';
        }}
        """

    elif archetype == "dna_pcr":
        return f"""
        function animateArchetype(result, values, pct) {{
            const nCycles = values['n'] !== undefined ? values['n'] : (values['cycles'] || Math.max(1, Math.min(40, Math.round(pct * 0.35 + 1))));
            const N0 = values['N0'] !== undefined ? values['N0'] : (values['N_0'] || 1);
            const temp = values['T'] !== undefined ? values['T'] : (values['temp'] || 72);

            const copies = (typeof result === 'number' && !isNaN(result) && result > 0) ? result : Math.min(1e15, N0 * Math.pow(2, nCycles));

            let stageName = '';
            let stageColor = '#10b981';
            let stageTemp = '72°C';
            let separationPx = 0;

            if (temp >= 88 || pct > 70) {{
                stageName = {is_ar_js} ? 'انفصال الشفرات (95°C)' : 'Denaturation (95°C)';
                stageColor = '#ef4444';
                stageTemp = '95°C';
                separationPx = 14;
            }} else if (temp <= 60 || pct < 35) {{
                stageName = {is_ar_js} ? 'ارتباط البادئات (55°C)' : 'Annealing (55°C)';
                stageColor = '#3b82f6';
                stageTemp = '55°C';
                separationPx = 6;
            }} else {{
                stageName = {is_ar_js} ? 'الاستطالة والنسخ (72°C)' : 'Extension (72°C)';
                stageColor = '#10b981';
                stageTemp = '72°C';
                separationPx = 2;
            }}

            const strandTop = document.getElementById('dna-strand-top');
            const strandBottom = document.getElementById('dna-strand-bottom');
            if (strandTop) strandTop.setAttribute('transform', 'translate(0, ' + (-separationPx).toFixed(1) + ')');
            if (strandBottom) strandBottom.setAttribute('transform', 'translate(0, ' + separationPx.toFixed(1) + ')');

            const taq = document.getElementById('taq-enzyme');
            if (taq) {{
                const taqX = 70 + (pct % 50) * 2.8;
                taq.setAttribute('transform', 'translate(' + taqX.toFixed(1) + ', 62)');
            }}

            const stageBadge = document.getElementById('pcr-stage-badge');
            if (stageBadge) {{
                stageBadge.textContent = stageName;
                stageBadge.setAttribute('fill', stageColor);
            }}

            const tempText = document.getElementById('pcr-temp-text');
            if (tempText) tempText.textContent = stageTemp;

            const cycleEl = document.getElementById('pcr-cycle-val');
            if (cycleEl) cycleEl.textContent = 'n = ' + nCycles;

            const copiesEl = document.getElementById('pcr-copies-val');
            if (copiesEl) copiesEl.textContent = formatNum(copies);

            const ampBar = document.getElementById('pcr-amplification-bar');
            if (ampBar) {{
                const logPct = Math.min(64, Math.max(4, Math.round((pct / 100) * 64)));
                ampBar.setAttribute('width', logPct.toString());
            }}
        }}
        """

    elif archetype == "ph_titration":
        return f"""
        function getPhColor(ph) {{
            if (ph < 3.0) return '#dc2626';
            if (ph < 6.0) return '#f97316';
            if (ph < 6.8) return '#eab308';
            if (ph <= 7.4) return '#10b981';
            if (ph <= 9.0) return '#06b6d4';
            if (ph <= 11.5) return '#3b82f6';
            return '#7c3aed';
        }}

        function animateArchetype(result, values, pct) {{
            const phVal = values['pH'] !== undefined ? values['pH'] : (values['ph'] !== undefined ? values['ph'] : Math.max(0, Math.min(14, result)));
            const vTitrant = values['V_base'] ?? values['V_titrant'] ?? values['Vb'] ?? values['Va'] ?? (pct * 0.5);

            const liq = document.getElementById('titration-liquid');
            if (liq) {{
                liq.setAttribute('fill', getPhColor(phVal));
            }}

            const drop = document.getElementById('titrant-drop');
            if (drop) {{
                drop.style.opacity = (0.3 + (pct % 25) / 25 * 0.7).toFixed(2);
            }}

            const readout = document.getElementById('ph-digital-readout');
            if (readout) {{
                readout.textContent = 'pH ' + formatNum(phVal);
                readout.setAttribute('fill', getPhColor(phVal));
            }}

            const badge = document.getElementById('ph-state-badge');
            if (badge) {{
                let phStatus = '';
                if (phVal < 3.0) phStatus = {is_ar_js} ? 'حمضي قوي (Strong Acid)' : 'Strong Acid';
                else if (phVal < 6.8) phStatus = {is_ar_js} ? 'حمضي ضعيف (Weak Acid)' : 'Weak Acid';
                else if (phVal <= 7.4) phStatus = {is_ar_js} ? 'متعادل (Neutral)' : 'Neutral';
                else if (phVal <= 11.0) phStatus = {is_ar_js} ? 'قاعدي ضعيف (Weak Base)' : 'Weak Base';
                else phStatus = {is_ar_js} ? 'قاعدي قوي (Strong Base)' : 'Strong Base';
                badge.textContent = phStatus;
                badge.setAttribute('fill', getPhColor(phVal));
            }}

            const volTxt = document.getElementById('titrant-vol-val');
            if (volTxt) {{
                volTxt.textContent = ({is_ar_js} ? 'الحجم المضاف: ' : 'V_added: ') + formatNum(vTitrant) + ' mL';
            }}
        }}
        """

    elif archetype == "cell_division":
        return f"""
        function animateArchetype(result, values, pct) {{
            let genVal = null;
            let genSym = 'n';
            if (values['g'] !== undefined) {{ genVal = values['g']; genSym = 'g'; }}
            else if (values['n'] !== undefined) {{ genVal = values['n']; genSym = 'n'; }}
            else if (values['gen'] !== undefined) {{ genVal = values['gen']; genSym = 'gen'; }}
            else if (values['t'] !== undefined) {{ genVal = values['t']; genSym = 't'; }}
            else {{
                const keys = Object.keys(values);
                if (keys.length > 1 && typeof values[keys[1]] === 'number') {{
                    genVal = values[keys[1]];
                    genSym = keys[1];
                }} else {{
                    genVal = Math.round((pct / 100) * 8);
                }}
            }}
            const genInt = Math.max(0, Math.round(genVal));

            const genEl = document.getElementById('division-gen-val');
            if (genEl) {{
                genEl.textContent = genSym + ' = ' + genInt;
            }}

            const totalEl = document.getElementById('division-total-cells');
            if (totalEl) {{
                totalEl.textContent = formatNum(result) + ({is_ar_js} ? ' خلية' : ' cells');
            }}

            const phaseBadge = document.getElementById('division-phase-badge');
            if (phaseBadge) {{
                let phaseTxt = '';
                let phaseCol = '#10b981';
                if (genInt === 0) {{
                    phaseTxt = {is_ar_js} ? 'طور التأقلم (Lag)' : 'Lag Phase';
                    phaseCol = '#94a3b8';
                }} else if (genInt <= 6) {{
                    phaseTxt = {is_ar_js} ? 'تضاعف أسي (Log)' : 'Exponential (Log)';
                    phaseCol = '#10b981';
                }} else {{
                    phaseTxt = {is_ar_js} ? 'طور الثبات (Stationary)' : 'Stationary Phase';
                    phaseCol = '#f59e0b';
                }}
                phaseBadge.textContent = phaseTxt;
                phaseBadge.setAttribute('fill', phaseCol);
            }}

            const b1 = document.getElementById('bact-cell-1');
            const b2 = document.getElementById('bact-cell-2');
            if (b1 && b2) {{
                const separation = Math.min(12, (pct / 100) * 12);
                b1.setAttribute('cx', (-4 - separation).toFixed(1));
                b2.setAttribute('cx', (4 + separation).toFixed(1));
            }}
            const dna1 = document.getElementById('bact-dna-1');
            const dna2 = document.getElementById('bact-dna-2');
            if (dna1 && dna2) {{
                const separation = Math.min(12, (pct / 100) * 12);
                dna1.setAttribute('cx', (-4 - separation).toFixed(1));
                dna2.setAttribute('cx', (4 + separation).toFixed(1));
            }}

            for (let i = 1; i <= 6; i++) {{
                const extra = document.getElementById('bact-extra-' + i);
                if (extra) {{
                    const thresh = i * 15;
                    const op = pct >= thresh ? Math.min(1.0, 0.3 + (pct - thresh) * 0.05) : 0.0;
                    extra.style.opacity = op.toFixed(2);
                }}
            }}
        }}
        """

    elif archetype == "enzyme_kinetics":
        return f"""
        function animateArchetype(result, values, pct) {{
            const sVal = values['S'] ?? values['[S]'] ?? values['s'] ?? values['conc'] ?? (pct * 0.5);
            const vmaxVal = values['Vmax'] ?? values['V_max'] ?? values['vmax'] ?? 100;
            const kmVal = values['Km'] ?? values['K_m'] ?? values['km'] ?? 10;
            const vVal = typeof result === 'number' && !isNaN(result) ? result : ((vmaxVal * sVal) / (kmVal + sVal));
            const satRatio = Math.min(1.0, Math.max(0.0, vVal / Math.max(vmaxVal, 0.001)));

            const vEl = document.getElementById('enzyme-v-val');
            if (vEl) vEl.textContent = 'v = ' + formatNum(vVal);

            const sEl = document.getElementById('enzyme-s-val');
            if (sEl) sEl.textContent = '[S] = ' + formatNum(sVal) + ' mM';

            const satBar = document.getElementById('enzyme-sat-bar');
            if (satBar) {{
                satBar.setAttribute('width', (satRatio * 120).toFixed(1));
            }}

            const activeGlow = document.getElementById('active-site-glow');
            if (activeGlow) {{
                activeGlow.setAttribute('opacity', (0.2 + satRatio * 0.7).toFixed(2));
                activeGlow.setAttribute('r', (12 + satRatio * 8).toFixed(1));
            }}

            const dock = document.getElementById('substrate-dock');
            if (dock) {{
                const dockX = 135 - satRatio * 28;
                dock.setAttribute('transform', 'translate(' + dockX.toFixed(1) + ', 70)');
            }}

            const badge = document.getElementById('enzyme-state-badge');
            if (badge) {{
                let badgeTxt = '';
                if (satRatio < 0.35) {{
                    badgeTxt = {is_ar_js} ? 'رتبة أولى ([S] << Km)' : '1st Order ([S] << Km)';
                }} else if (satRatio < 0.75) {{
                    badgeTxt = {is_ar_js} ? 'حركية مختلطة (v ~ Vmax/2)' : 'Mixed Kinetics (v ~ Vmax/2)';
                }} else {{
                    badgeTxt = {is_ar_js} ? 'تشبع كامل بالركيزة (رتبة صفرية)' : 'Enzyme Saturated (Zero Order)';
                }}
                badge.textContent = badgeTxt;
            }}
        }}
        """

    elif archetype == "thermo_calorimeter":
        return f"""
        function animateArchetype(result, values, pct) {{
            const dtVal = values['ΔT'] ?? values['dT'] ?? values['dt'] ?? values['T'] ?? (pct * 0.5 - 25);
            const mVal = values['m'] ?? values['mass'] ?? 100;
            const cVal = values['c'] ?? values['C'] ?? values['cp'] ?? 4.184;
            const qVal = typeof result === 'number' && !isNaN(result) ? result : (mVal * cVal * dtVal);

            const qEl = document.getElementById('calorimeter-q-val');
            if (qEl) qEl.textContent = 'q = ' + formatNum(qVal) + ' J';

            const tEl = document.getElementById('calorimeter-temp-val');
            if (tEl) tEl.textContent = 'ΔT = ' + (dtVal >= 0 ? '+' : '') + formatNum(dtVal) + ' °C';

            const merc = document.getElementById('calorimeter-mercury');
            if (merc) {{
                const mercH = Math.max(6, Math.min(85, 15 + (pct / 100) * 65));
                merc.setAttribute('height', mercH.toFixed(1));
                merc.setAttribute('y', (114 - mercH).toFixed(1));
            }}

            const stop1 = document.getElementById('calor-grad-stop1');
            const stop2 = document.getElementById('calor-grad-stop2');
            const isExo = qVal >= 0 || dtVal >= 0;

            if (stop1 && stop2) {{
                if (isExo) {{
                    stop1.setAttribute('stop-color', '#f97316');
                    stop2.setAttribute('stop-color', '#dc2626');
                }} else {{
                    stop1.setAttribute('stop-color', '#38bdf8');
                    stop2.setAttribute('stop-color', '#4338ca');
                }}
            }}

            const badge = document.getElementById('calorimeter-state-badge');
            if (badge) {{
                const badgeTxt = isExo
                    ? ({is_ar_js} ? 'طارد للحرارة (Exothermic)' : 'Exothermic (ΔH < 0)')
                    : ({is_ar_js} ? 'ماص للحرارة (Endothermic)' : 'Endothermic (ΔH > 0)');
                badge.textContent = badgeTxt;
                badge.setAttribute('fill', isExo ? '#ef4444' : '#38bdf8');
            }}

            const stirrer = document.getElementById('calorimeter-stirrer-group');
            if (stirrer) {{
                const oscX = Math.sin((pct * 0.2)) * 3;
                stirrer.setAttribute('transform', 'translate(' + oscX.toFixed(1) + ', 0)');
            }}
        }}
        """

    else:
        return "function animateArchetype(result, values, pct) {}"



def render_slider_lab(spec: SimulationSpec) -> str:
    """
    Renders an interactive HTML5 micro-lab for continuous equation and physical exploration.
    Supports authentic scientific visual archetypes and generative visual SVG models.

    Parameters:
        spec: SimulationSpec with engine_type=EngineType.SLIDER.

    Returns:
        A self-contained HTML5 string (<25KB) with inline CSS, SVG, and JS.

    Raises:
        ValueError: If engine_type is not SLIDER, or if variables or formula are empty.
    """
    if spec.engine_type != EngineType.SLIDER:
        raise ValueError("Expected SLIDER engine type")

    if not spec.variables:
        raise ValueError("SLIDER engine requires at least one variable")

    if not spec.formula_expression or not spec.formula_expression.strip():
        raise ValueError("SLIDER engine requires formula_expression")

    # Detect language direction
    is_ar = _is_arabic(spec.title) or any(_is_arabic(v.get("name", "")) for v in spec.variables)
    direction = "rtl" if is_ar else "ltr"
    lang = "ar" if is_ar else "en"

    # Detect visual archetype
    archetype = _detect_archetype(spec)

    # Clean formula expression
    clean_formula = spec.formula_expression.strip().replace("==", "=")
    all_syms = [v.get("symbol", "") for v in spec.variables if v.get("symbol")]

    is_equilibrium = False
    lhs_expr = ""
    rhs_expr = clean_formula
    result_symbol = "Result"
    result_unit = ""

    if "=" in clean_formula:
        parts = clean_formula.split("=", 1)
        lhs_cand = parts[0].strip()
        rhs_cand = parts[1].strip()

        lhs_has_vars = any(s and s in lhs_cand for s in all_syms)
        rhs_has_vars = any(s and s in rhs_cand for s in all_syms)

        if lhs_has_vars and rhs_has_vars and any(k in clean_formula.lower() for k in ["d1", "d2", "arm", "fulcrum", "torque", "عزم", "lever", "رافعة"]):
            is_equilibrium = True
            lhs_expr = lhs_cand
            rhs_expr = rhs_cand

        else:
            is_equilibrium = False
            result_symbol = lhs_cand
            rhs_expr = rhs_cand
            lhs_expr = ""

    # Decouple dependent result variable from independent slider inputs
    result_var = None
    candidate_slider_vars = []
    if not is_equilibrium:
        for v in spec.variables:
            sym = v.get("symbol", "")
            if sym == result_symbol or sym.strip("[]") == result_symbol.strip("[]"):
                result_var = v
            else:
                candidate_slider_vars.append(v)
    else:
        candidate_slider_vars = list(spec.variables)

    # Dependency Graph Pruner: eliminate any disconnected Zombie / Dummy variables
    active_eval_expr = (rhs_expr + " " + lhs_expr) if is_equilibrium else rhs_expr
    active_slider_vars = [
        v for v in candidate_slider_vars
        if _is_variable_active(v, active_eval_expr, spec.svg_bindings, archetype)
    ]

    # Safeguard: if filtering would leave 0 sliders, keep candidate_slider_vars or result_var
    if active_slider_vars:
        slider_vars = active_slider_vars
    elif candidate_slider_vars:
        slider_vars = candidate_slider_vars
    elif result_var:
        slider_vars = [result_var]
    else:
        slider_vars = list(spec.variables)

    result_unit = getattr(spec, "result_unit", "") or ""
    if not result_unit and result_var:
        result_unit = result_var.get("unit", "")
    if not result_unit:
        for v in spec.variables:
            if v.get("symbol") == result_symbol:
                result_unit = v.get("unit", "")
                break
    if not result_unit:
        sym_l = result_symbol.strip().lower()
        if sym_l in ("f", "fg", "fe", "force"):
            result_unit = "N"
        elif sym_l in ("v", "speed", "velocity"):
            result_unit = "m/s"
        elif sym_l in ("a", "acc", "acceleration"):
            result_unit = "m/s²"
        elif sym_l in ("p", "pressure"):
            result_unit = "atm" if archetype == "piston" else "Pa"
        elif sym_l in ("l", "λ", "lambda", "wavelength", "r", "d", "x"):
            result_unit = "m"
        elif sym_l in ("t", "period", "time"):
            result_unit = "s"

    # Single Source of Truth: bounds are always pre-computed deterministically in pair2_interactive
    expected_min = float(getattr(spec, "result_min", 0.0))
    expected_max = float(getattr(spec, "result_max", 100.0))
    is_log_scale = bool(getattr(spec, "is_logarithmic_output", False))
    ratio = (expected_max / max(expected_min, 1.0)) if expected_max > 0 else 1.0
    if any(k in clean_formula.lower() for k in ["pow(", "**", "^"]) or ratio > 1e6:
        is_log_scale = True
    if expected_max <= expected_min:
        expected_max = expected_min + (abs(expected_min) if expected_min != 0 else 10.0)
    if hasattr(spec, "result_symbol") and spec.result_symbol and spec.result_symbol != "Result":
        result_symbol = spec.result_symbol
    elif lhs_cand:
        result_symbol = lhs_cand

    # Build slider controls HTML with index-safe identifiers
    slider_rows = []
    vars_meta = []
    for idx, var in enumerate(slider_vars):
        sym = var.get("symbol", f"x_{idx}")
        name = var.get("name", sym)
        unit = var.get("unit", "")
        min_v = float(var.get("min_val", 0.0))
        max_v = float(var.get("max_val", 100.0))
        def_v = float(var.get("default_val", (min_v + max_v) / 2.0))

        vars_meta.append({
            "index": idx,
            "symbol": sym,
            "name": name,
            "unit": unit,
            "min_val": min_v,
            "max_val": max_v,
            "default_val": def_v,
        })

        span = max_v - min_v
        step_val = (span / 1000.0) if span > 0 else 0.001
        step = f"{step_val:.6g}"

        clean_def = _clean_num(def_v)
        safe_sym = sym.replace("'", "\\'").replace('"', '&quot;')
        row = f"""
        <div class="slider-group">
            <div class="slider-header">
                <span class="var-title"><strong>{name}</strong> ({sym})</span>
                <span class="var-val"><span id="val-{sym}" data-val-idx="{idx}">{clean_def}</span> <small>{unit}</small></span>
            </div>
            <input type="range" id="slider-{sym}" data-idx="{idx}" min="{min_v}" max="{max_v}" step="{step}" value="{def_v}"
                   oninput="updateLab({idx}, '{safe_sym}')" aria-label="{name}">
        </div>
        """
        slider_rows.append(row)

    sliders_html = "\n".join(slider_rows)
    vars_meta_json = json.dumps(vars_meta, ensure_ascii=False)
    symbols_json = json.dumps([v.get("symbol") for v in slider_vars if v.get("symbol")], ensure_ascii=False)
    constants_json = json.dumps(spec.constants or {}, ensure_ascii=False)
    lhs_expr_json = json.dumps(lhs_expr, ensure_ascii=False)
    rhs_expr_json = json.dumps(rhs_expr, ensure_ascii=False)
    bindings_json = json.dumps(spec.svg_bindings or {}, ensure_ascii=False)
    is_eq_js = "true" if is_equilibrium else "false"
    bound_min_json = json.dumps(expected_min)
    bound_max_json = json.dumps(expected_max)
    is_log_scale_js = "true" if is_log_scale else "false"
    result_unit_json = json.dumps(result_unit, ensure_ascii=False)
    result_symbol_json = json.dumps(result_symbol, ensure_ascii=False)

    formula_label = "المعادلة الرياضية" if is_ar else "Mathematical Formula"
    effort_label = "عزم الجهد (الطرف الأيسر)" if is_ar else "Effort Side (LHS)"
    load_label = "عزم الحمل (الطرف الأيمن)" if is_ar else "Load Side (RHS)"

    # Set contextual result labels based on archetype or variable name
    res_custom_name = result_var.get("name") if result_var else None
    if res_custom_name and res_custom_name.strip() and res_custom_name.strip() != result_symbol:
        res_display_title = res_custom_name.strip()
    else:
        res_display_title = None

    if is_ar:
        if res_display_title:
            result_label = f"{res_display_title} ({result_symbol})"
        else:
            result_label = f"النتيجة المحسوبة ({result_symbol})"
        metric_sub = "المحاكاة العلمية التفاعلية"
    else:
        if res_display_title:
            result_label = f"{res_display_title} ({result_symbol})"
        else:
            result_label = f"Calculated Result ({result_symbol})"
        metric_sub = "Interactive STEM Simulation"

    # Visual SVG Block & JS runtime for archetype
    if spec.visual_svg and spec.visual_svg.strip() and "<svg" in spec.visual_svg:
        visual_svg_block = f'<div class="visual-display">{spec.visual_svg}</div>'
    else:
        visual_svg_block = _render_archetype_svg(archetype, is_ar)
    archetype_js = _get_archetype_js(archetype, is_ar)

    # Dual display for Equilibrium vs Single display for direct laws
    if is_equilibrium:
        display_section = f"""
        <div class="dual-card-grid">
            <div class="card-side effort-side">
                <div class="formula-tag">{effort_label}</div>
                <div class="result-number" id="result-lhs">0.00</div>
                <div class="side-expr">{lhs_expr}</div>
            </div>
            <div class="status-middle">
                <div class="balance-badge" id="balance-badge">...</div>
            </div>
            <div class="card-side load-side">
                <div class="formula-tag">{load_label}</div>
                <div class="result-number" id="result-rhs">0.00</div>
                <div class="side-expr">{rhs_expr}</div>
            </div>
        </div>

        {visual_svg_block}

        <div class="balance-bar-container">
            <div class="balance-bar-track">
                <div id="balance-bar-fill" class="balance-bar-fill" style="width: 50%;"></div>
            </div>
            <div class="balance-bar-text" id="balance-bar-label">50% Balance</div>
        </div>
        """
    else:
        unit_str = f" <small>{result_unit}</small>" if result_unit else ""
        display_section = f"""
        <div class="result-card">
            <div class="formula-tag">{result_label}</div>
            <div class="result-number"><span id="result-display">0.00</span>{unit_str}</div>
            <div class="result-subtext">{metric_sub}</div>
        </div>

        {visual_svg_block}

        <div class="balance-bar-container" style="width: 100%; max-width: 360px;">
            <div class="balance-bar-track">
                <div id="visual-bar" class="balance-bar-fill" style="width: 50%;"></div>
            </div>
            <div class="balance-bar-text" id="visual-text">50% Scale</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="{lang}" dir="{direction}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec.title}</title>
    <style>
        :root {{
            --bg: #f0f4f8; --card: #ffffff; --primary: #4f46e5;
            --accent: #10b981; --amber: #f59e0b; --text: #1e293b; --muted: #475569;
        }}
        *{{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Noto Sans Arabic','Helvetica Neue',sans-serif;letter-spacing:0.015em;}}
        body{{background:var(--bg);color:var(--text);padding:10px;font-size:13.5px;line-height:1.55;-webkit-font-smoothing:antialiased;}}
        .lab-container{{max-width:620px;margin:0 auto;background:var(--card);border-radius:12px;padding:14px;box-shadow:0 6px 18px rgba(0,0,0,0.06);border:1px solid #e2e8f0;}}
        h1{{font-size:18.5px;font-weight:800;color:var(--primary);text-align:center;margin-bottom:8px;letter-spacing:0.02em;}}
        .formula-box{{background:#e0e7ff;border-radius:8px;padding:6px 10px;text-align:center;margin-bottom:10px;border:1px solid #c7d2fe;}}
        .formula-tag{{font-size:10px;color:var(--muted);text-transform:uppercase;font-weight:700;letter-spacing:0.025em;}}
        .formula-text{{font-size:16px;font-weight:800;color:var(--primary);margin-top:2px;letter-spacing:0.02em;}}
        .dual-card-grid{{display:grid;grid-template-columns:1fr auto 1fr;gap:6px;align-items:center;margin-bottom:10px;}}
        .card-side{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:6px;text-align:center;}}
        .effort-side{{border-inline-start:3px solid #3b82f6;}}.load-side{{border-inline-end:3px solid #f59e0b;}}
        .side-expr{{font-size:10.5px;color:var(--muted);font-weight:600;}}
        .status-middle{{display:flex;justify-content:center;align-items:center;}}
        .balance-badge{{padding:4px 8px;border-radius:12px;font-size:11px;font-weight:800;white-space:nowrap;letter-spacing:0.015em;}}
        .balance-badge.balanced{{background:#d1fae5;color:#065f46;border:1px solid #6ee7b7;}}
        .balance-badge.tilt-left{{background:#dbeafe;color:#1e40af;border:1px solid #93c5fd;}}
        .balance-badge.tilt-right{{background:#fef3c7;color:#92400e;border:1px solid #fde68a;}}
        .result-card{{background:#f8fafc;border:2px dashed #cbd5e1;border-radius:8px;padding:8px;text-align:center;margin-bottom:10px;}}
        .result-number{{font-size:22px;font-weight:800;color:var(--accent);margin:2px 0;font-variant-numeric:tabular-nums;}}
        .result-subtext{{font-size:11px;color:var(--muted);font-weight:600;letter-spacing:0.015em;}}
        .visual-display{{display:flex;justify-content:center;align-items:center;margin-bottom:10px;}}
        svg{{max-width:100%;height:auto;}}
        .balance-bar-container{{margin:0 auto 10px auto;max-width:320px;}}
        .balance-bar-track{{background:#e2e8f0;height:10px;border-radius:5px;overflow:hidden;}}
        .balance-bar-fill{{height:100%;border-radius:5px;background:var(--accent);transition:width 0.15s ease-out;}}
        .balance-bar-text{{text-align:center;font-size:11.5px;font-weight:700;color:var(--muted);margin-top:2px;letter-spacing:0.015em;}}
        .sliders-section{{display:flex;flex-direction:column;gap:8px;}}
        .slider-group{{background:#f8fafc;border-radius:6px;padding:6px 10px;border:1px solid #e2e8f0;}}
        .slider-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;font-size:13.5px;letter-spacing:0.015em;}}
        .var-val{{font-weight:700;color:var(--primary);font-variant-numeric:tabular-nums;}}
        input[type="range"]{{width:100%;height:5px;border-radius:3px;background:#cbd5e1;outline:none;cursor:pointer;accent-color:var(--primary);}}
    </style>
</head>
<body>
    <div class="lab-container">
        <h1>{spec.title}</h1>
        <div class="formula-box">
            <div class="formula-tag">{formula_label}</div>
            <div class="formula-text">{clean_formula}</div>
        </div>
        {display_section}
        <div class="sliders-section">
            {sliders_html}
        </div>
    </div>

    <script>
        const varsMeta = {vars_meta_json};
        const symbols = {symbols_json};
        const constants = {constants_json};
        const isEquilibrium = {is_eq_js};
        const lhsExpr = {lhs_expr_json};
        const rhsExpr = {rhs_expr_json};
        const archetype = "{archetype}";
        const bindings = {bindings_json};
        const isArabic = "{lang}" === "ar";
        let boundMin = {bound_min_json};
        let boundMax = {bound_max_json};
        const isLogScale = {is_log_scale_js};
        let useLogScale = isLogScale;
        const resultUnit = {result_unit_json};
        const resultSymbol = {result_symbol_json};

        function escapeRegExp(str) {{
            return str.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
        }}

        function normalizeChemSymbols(str) {{
            if (!str) return "";
            return str
                .replace(/[⁻−﹣－]/g, '-')
                .replace(/[⁺﹢＋]/g, '+');
        }}

        function safeReplace(expr, symList, valMap) {{
            if (!expr) return "0";
            let s = normalizeChemSymbols(expr)
                .replace(/×/g, '*')
                .replace(/÷/g, '/')
                .replace(/·/g, '*')
                .replace(/−/g, '-')
                .replace(/==/g, '=')
                .replace(/\\^/g, '**');

            s = s.replace(/\\*\\*\\s*-\\s*([0-9.]+)/g, '** (-$1)');

            const allSyms = [...new Set([...(symList || []), ...Object.keys(constants || {{}})])];
            const sorted = allSyms.sort((a, b) => (b ? b.length : 0) - (a ? a.length : 0));
            for (const rawSym of sorted) {{
                if (!rawSym) continue;
                const sym = normalizeChemSymbols(rawSym);
                let val = 0;
                if (valMap && valMap[rawSym] !== undefined && !isNaN(valMap[rawSym])) {{
                    val = valMap[rawSym];
                }} else if (valMap && valMap[sym] !== undefined && !isNaN(valMap[sym])) {{
                    val = valMap[sym];
                }} else if (constants && constants[rawSym] !== undefined && !isNaN(constants[rawSym])) {{
                    val = constants[rawSym];
                }} else if (constants && constants[sym] !== undefined && !isNaN(constants[sym])) {{
                    val = constants[sym];
                }}

                const escaped = escapeRegExp(sym);
                const startsWord = /^[\\w\\u0600-\\u06FF]/.test(sym);
                const endsWord = /[\\w\\u0600-\\u06FF]$/.test(sym);
                const lb = startsWord ? "(?<![\\\\w\\\\u0600-\\\\u06FF\\\\u2070-\\\\u209F])" : "";
                const la = endsWord ? "(?![\\\\w\\\\u0600-\\\\u06FF\\\\u2070-\\\\u209F])" : "";

                try {{
                    const re = new RegExp(lb + escaped + la, "gu");
                    s = s.replace(re, "(" + val + ")");
                }} catch (reErr) {{
                    s = s.split(sym).join("(" + val + ")");
                }}
            }}

            const fns = ["pow", "sqrt", "cbrt", "log10", "log2", "log", "ln", "exp", "abs", "sin", "cos", "tan", "asin", "acos", "atan", "min", "max", "round", "floor", "ceil"];
            for (const fn of fns) {{
                const re = new RegExp('\\\\b' + fn + '\\\\s*\\\\(', 'gi');
                const target = (fn.toLowerCase() === 'ln') ? 'Math.log(' : ('Math.' + fn + '(');
                s = s.replace(re, target);
            }}

            s = s.replace(/\\b(?:PI|pi|π)\\b/g, 'Math.PI');

            return s;
        }}

        function safeEval(exprStr) {{
            try {{
                const safeMath = Object.create(Math);
                safeMath.log10 = (x) => Math.log10(Math.max(1e-9, Number(x) || 1e-9));
                safeMath.log = (x) => Math.log(Math.max(1e-9, Number(x) || 1e-9));
                safeMath.sqrt = (x) => Math.sqrt(Math.max(0, Number(x) || 0));

                let guarded = exprStr
                    .replace(/\\/\\s*\\(\\s*0(?:\\.0+)?\\s*\\)/g, '/ (1e-6)')
                    .replace(/\\/\\s*0(?:\\.0+)?(?![0-9.])/g, '/ 1e-6');

                const res = Function("Math", '"use strict"; return (' + guarded + ');')(safeMath);
                if (typeof res === 'number') {{
                    if (isNaN(res)) return 0;
                    if (!isFinite(res)) return res > 0 ? 999999 : -999999;
                    return res;
                }}
                return 0;
            }} catch (err) {{
                return 0;
            }}
        }}

        function formatNum(n) {{
            if (typeof n !== 'number' || isNaN(n) || !isFinite(n)) return '0';
            const absN = Math.abs(n);
            if (absN === 0) return '0';
            if (absN >= 1000000 || (absN < 0.0001 && absN > 0)) {{
                return n.toExponential(2);
            }}
            if (absN < 1) {{
                return parseFloat(n.toPrecision(3)).toString();
            }}
            return (n % 1 === 0) ? n.toFixed(0) : parseFloat(n.toFixed(2)).toString();
        }}

        {archetype_js}

        function autoCalibrateBounds() {{
            if (isEquilibrium || !rhsExpr || !varsMeta || varsMeta.length === 0) return;
            if (boundMin === 0 && boundMax === 14) return;
            if (boundMin === 0 && boundMax === 100 && (rhsExpr.includes('100 *') || rhsExpr.includes('* 100') || (lhsExpr && lhsExpr.toLowerCase().includes('v_cell')))) return;

            const grid = [];
            const activeVars = varsMeta.slice(0, 4);
            activeVars.forEach(v => {{
                let el = null;
                try {{
                    el = v.symbol ? document.getElementById('slider-' + v.symbol) : null;
                }} catch (_) {{}}
                if (!el) {{
                    el = document.querySelector('input[data-idx="' + v.index + '"]');
                }}
                let mn = (el && el.min !== "" && !isNaN(parseFloat(el.min))) ? parseFloat(el.min) : (typeof v.min_val === 'number' ? v.min_val : 0);
                let mx = (el && el.max !== "" && !isNaN(parseFloat(el.max))) ? parseFloat(el.max) : (typeof v.max_val === 'number' ? v.max_val : 100);
                if (mn >= mx) mx = mn + 10;
                const step = (mx - mn) / 4;
                grid.push([mn, mn + step, mn + 2 * step, mn + 3 * step, mx]);
            }});

            const samples = [];
            function cartesian(idx, current) {{
                if (idx === grid.length) {{
                    const valMap = Object.assign({{}}, current);
                    varsMeta.slice(4).forEach(v => {{
                        valMap[v.symbol] = v.default_val !== undefined ? v.default_val : v.min_val;
                    }});
                    const s = safeReplace(rhsExpr, symbols, valMap);
                    const res = safeEval(s);
                    if (typeof res === 'number' && !isNaN(res) && isFinite(res)) {{
                        samples.push(res);
                    }}
                    return;
                }}
                for (let i = 0; i < grid[idx].length; i++) {{
                    current[activeVars[idx].symbol] = grid[idx][i];
                    cartesian(idx + 1, current);
                }}
            }}

            cartesian(0, {{}});

            if (samples.length > 0) {{
                let trueMin = Math.min(...samples);
                let trueMax = Math.max(...samples);
                if (trueMax > trueMin) {{
                    boundMin = trueMin;
                    boundMax = trueMax;
                }}
            }}

            const midMap = {{}};
            varsMeta.forEach(v => {{
                let el = null;
                try {{
                    el = v.symbol ? document.getElementById('slider-' + v.symbol) : null;
                }} catch (_) {{}}
                if (!el) {{
                    el = document.querySelector('input[data-idx="' + v.index + '"]');
                }}
                let mn = (el && el.min !== "" && !isNaN(parseFloat(el.min))) ? parseFloat(el.min) : (typeof v.min_val === 'number' ? v.min_val : 0);
                let mx = (el && el.max !== "" && !isNaN(parseFloat(el.max))) ? parseFloat(el.max) : (typeof v.max_val === 'number' ? v.max_val : 100);
                if (mn >= mx) mx = mn + 10;
                midMap[v.symbol] = mn + (mx - mn) * 0.5;
            }});
            const midExprStr = safeReplace(rhsExpr, symbols, midMap);
            const midVal = safeEval(midExprStr);

            if (boundMax > boundMin && boundMin >= 0 && boundMax > 0) {{
                const linSpan = boundMax - boundMin;
                const midRatio = (midVal - boundMin) / linSpan;
                const maxRatio = boundMax / Math.max(boundMin, 1e-6);
                if (midRatio < 0.08 || (boundMin > 0 && maxRatio > 200)) {{
                    useLogScale = true;
                }}
            }}
        }}

        autoCalibrateBounds();

        function calculate() {{
            try {{
                const values = {{}};
                varsMeta.forEach(v => {{
                    let el = null;
                    try {{
                        el = (v.symbol ? document.getElementById('slider-' + v.symbol) : null);
                    }} catch (_) {{}}
                    if (!el) {{
                        el = document.querySelector('input[data-idx="' + v.index + '"]');
                    }}
                    values[v.symbol] = el ? parseFloat(el.value) : 0;
                }});

                if (isEquilibrium) {{
                    const sL = safeReplace(lhsExpr, symbols, values);
                    const sR = safeReplace(rhsExpr, symbols, values);
                    const valL = safeEval(sL);
                    const valR = safeEval(sR);

                    const elL = document.getElementById('result-lhs');
                    const elR = document.getElementById('result-rhs');
                    if (elL) elL.textContent = formatNum(valL);
                    if (elR) elR.textContent = formatNum(valR);

                    const maxRef = Math.max(Math.abs(valL), Math.abs(valR), 0.001);
                    const diff = valR - valL;
                    const diffRatio = diff / maxRef;

                    const beamGroup = document.getElementById('lever-beam-group');
                    if (beamGroup) {{
                        const angle = Math.max(-16, Math.min(16, diffRatio * 16));
                        beamGroup.setAttribute('transform', 'rotate(' + angle.toFixed(1) + ', 180, 56)');
                    }}

                    const balanceRatio = Math.max(0, Math.min(100, Math.round((Math.min(valL, valR) / maxRef) * 100)));
                    const badge = document.getElementById('balance-badge');
                    const barFill = document.getElementById('balance-bar-fill');
                    const barLabel = document.getElementById('balance-bar-label');

                    const isBalanced = Math.abs(valL - valR) <= 0.025 * maxRef;

                    if (isBalanced) {{
                        if (badge) {{
                            badge.className = 'balance-badge balanced';
                            badge.textContent = isArabic ? '✓ متزن تماماً' : '✓ Balanced';
                        }}
                        if (barFill) {{
                            barFill.style.background = '#10b981';
                            barFill.style.width = '100%';
                        }}
                        if (barLabel) {{
                            barLabel.textContent = isArabic ? '100% اتزان تام' : '100% Balanced';
                        }}
                    }} else if (valL > valR) {{
                        if (badge) {{
                            badge.className = 'balance-badge tilt-left';
                            badge.textContent = isArabic ? '← رجحان الجهد' : '← Effort Dominates';
                        }}
                        if (barFill) {{
                            barFill.style.background = '#3b82f6';
                            barFill.style.width = balanceRatio + '%';
                        }}
                        if (barLabel) {{
                            barLabel.textContent = balanceRatio + '% ' + (isArabic ? 'نسبة الاتزان' : 'Balance');
                        }}
                    }} else {{
                        if (badge) {{
                            badge.className = 'balance-badge tilt-right';
                            badge.textContent = isArabic ? 'رجحان الحمل →' : 'Load Dominates →';
                        }}
                        if (barFill) {{
                            barFill.style.background = '#f59e0b';
                            barFill.style.width = balanceRatio + '%';
                        }}
                        if (barLabel) {{
                            barLabel.textContent = balanceRatio + '% ' + (isArabic ? 'نسبة الاتزان' : 'Balance');
                        }}
                    }}
                }} else {{
                    const s = safeReplace(rhsExpr, symbols, values);
                    const result = safeEval(s);

                    const resDisp = document.getElementById('result-display');
                    if (resDisp) resDisp.textContent = formatNum(result);

                    const bar = document.getElementById('visual-bar');
                    const vText = document.getElementById('visual-text');

                    if (result < boundMin) boundMin = result;
                    if (result > boundMax) boundMax = result;

                    let pct = 50;
                    if (boundMax > boundMin) {{
                        const isExp = useLogScale || (rhsExpr && (rhsExpr.includes('pow(') || rhsExpr.includes('**')));
                        if (isExp && boundMin >= 0 && boundMax > 0) {{
                            const safeMin = Math.max(boundMin, 1e-6);
                            const logMin = Math.log10(safeMin);
                            const logMax = Math.log10(boundMax);
                            const logVal = Math.log10(Math.max(result, safeMin));
                            pct = Math.min(100, Math.max(0, ((logVal - logMin) / (logMax - logMin)) * 100));
                        }} else {{
                            pct = ((result - boundMin) / (boundMax - boundMin)) * 100;
                        }}
                    }}
                    pct = Math.round(Math.max(0, Math.min(100, pct)));

                    if (bar) {{
                        bar.style.width = pct + '%';
                        if (archetype === 'ph_titration' || (archetype === 'beaker' && resultSymbol && resultSymbol.toLowerCase() === 'ph')) {{
                            if (typeof getPhColor === 'function') {{
                                bar.style.background = getPhColor(result);
                            }}
                        }}
                    }}
                    if (vText) {{
                        const unitSuffix = (typeof resultUnit !== 'undefined' && resultUnit) ? (' ' + resultUnit) : '';
                        const symPrefix = (typeof resultSymbol !== 'undefined' && resultSymbol && resultSymbol !== 'Result') ? (resultSymbol + ' = ') : '';
                        if (archetype === 'ph_titration' || (archetype === 'beaker' && resultSymbol && resultSymbol.toLowerCase() === 'ph')) {{
                            const phStatus = isArabic ? (result < 6.8 ? 'حمضي' : (result > 7.4 ? 'قاعدي' : 'متعادل')) : (result < 6.8 ? 'Acidic' : (result > 7.4 ? 'Basic' : 'Neutral'));
                            vText.textContent = pct + '% (pH ' + formatNum(result) + ' • ' + phStatus + ')';
                        }} else {{
                            vText.textContent = pct + '% (' + symPrefix + formatNum(result) + unitSuffix + ')';
                        }}
                    }}

                    if (typeof animateArchetype === 'function') {{
                        animateArchetype(result, values, pct);
                    }}

                    if (bindings && typeof bindings === 'object') {{
                        for (const [key, binding] of Object.entries(bindings)) {{
                            if (!binding || !binding.element_id) continue;
                            const elem = document.getElementById(binding.element_id);
                            if (!elem) continue;
                            const vVal = values[key] !== undefined ? values[key] : result;
                            if (binding.attribute) {{
                                const scale = binding.scale !== undefined ? binding.scale : 1;
                                const base = binding.base !== undefined ? binding.base : 0;
                                elem.setAttribute(binding.attribute, (base + vVal * scale).toFixed(1));
                            }}
                        }}
                    }}
                }}
            }} catch (calcErr) {{
                console.error("Simulation calculate error:", calcErr);
            }}
        }}

        function updateLab(idx, sym) {{
            try {{
                let input = null;
                try {{
                    input = (sym ? document.getElementById('slider-' + sym) : null);
                }} catch (_) {{}}
                if (!input) {{
                    input = document.querySelector('input[data-idx="' + idx + '"]');
                }}

                let valSpan = null;
                try {{
                    valSpan = (sym ? document.getElementById('val-' + sym) : null);
                }} catch (_) {{}}
                if (!valSpan) {{
                    valSpan = document.querySelector('[data-val-idx="' + idx + '"]');
                }}

                if (input && valSpan) {{
                    valSpan.textContent = formatNum(parseFloat(input.value));
                }}
                calculate();
            }} catch (updErr) {{
                console.error("Update slider error:", updErr);
            }}
        }}

        calculate();
    </script>
</body>
</html>"""
    return html
