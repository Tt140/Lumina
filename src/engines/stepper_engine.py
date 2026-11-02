"""LuminaLab Swarm - Universal Stepper Engine (HTML5/Canvas/CSS)."""

import json
from src.contracts.schemas import SimulationSpec, EngineType


def _is_arabic(text: str) -> bool:
    """Check if the text contains Arabic characters."""
    return any('\u0600' <= ch <= '\u06FF' for ch in text)


def render_stepper_lab(spec: SimulationSpec) -> str:
    """
    Renders an interactive HTML5 micro-lab for step-by-step algorithms and sequential processes.

    Parameters:
        spec: SimulationSpec with engine_type=EngineType.STEPPER.

    Returns:
        A self-contained HTML5 string (<25KB) with inline CSS and JS.

    Raises:
        ValueError: If engine_type is not STEPPER or steps list is empty.
    """
    if spec.engine_type != EngineType.STEPPER:
        raise ValueError("Expected STEPPER engine type")

    if not spec.steps:
        raise ValueError("STEPPER engine requires at least one step")

    # Detect language direction
    is_ar = _is_arabic(spec.title) or any(_is_arabic(s.get("label", "")) for s in spec.steps)
    direction = "rtl" if is_ar else "ltr"
    lang = "ar" if is_ar else "en"

    # Localization labels
    prev_label = "⏮ السابق" if is_ar else "⏮ Prev"
    next_label = "التالي ⏭" if is_ar else "Next ⏭"
    play_label = "▶ تشغيل" if is_ar else "▶ Play"
    pause_label = "⏸ إيقاف" if is_ar else "⏸ Pause"
    step_word = "الخطوة" if is_ar else "Step"
    of_word = "من" if is_ar else "of"
    state_label = "حالة النظام" if is_ar else "System State"

    steps_json = json.dumps(spec.steps, ensure_ascii=False)

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
            --primary: #4338ca;
            --primary-light: #e0e7ff;
            --accent: #0ea5e9;
            --success: #10b981;
            --warning: #f59e0b;
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
            margin-bottom: 20px;
        }}
        .progress-wrapper {{
            margin-bottom: 20px;
        }}
        .progress-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            color: var(--text-muted);
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .progress-bar-bg {{
            height: 10px;
            background: #e2e8f0;
            border-radius: 5px;
            overflow: hidden;
        }}
        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--primary));
            width: 0%;
            transition: width 0.3s ease;
        }}
        .step-card {{
            background: #f1f5f9;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #cbd5e1;
            min-height: 130px;
            transition: opacity 0.25s ease;
        }}
        .step-label {{
            font-size: 20px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 8px;
        }}
        .step-desc {{
            font-size: 16px;
            color: var(--text-main);
            line-height: 1.6;
        }}
        .state-container {{
            background: #ffffff;
            border: 2px dashed #cbd5e1;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
        }}
        .state-header {{
            font-size: 13px;
            text-transform: uppercase;
            font-weight: 700;
            color: var(--text-muted);
            margin-bottom: 12px;
        }}
        .array-view {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
            margin-bottom: 12px;
        }}
        .array-box {{
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f8fafc;
            border: 2px solid #94a3b8;
            border-radius: 8px;
            font-weight: bold;
            font-size: 18px;
            transition: all 0.2s ease;
            position: relative;
        }}
        .array-box.highlight {{
            background: #fef3c7;
            border-color: var(--warning);
            color: #b45309;
            transform: translateY(-2px);
        }}
        .array-box.found {{
            background: #d1fae5;
            border-color: var(--success);
            color: #065f46;
            transform: scale(1.05);
        }}
        .array-box.dimmed {{
            opacity: 0.35;
        }}
        .state-badges {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }}
        .state-pill {{
            background: var(--primary-light);
            color: var(--primary);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
        }}
        .controls-row {{
            display: flex;
            gap: 12px;
            justify-content: center;
        }}
        .btn {{
            padding: 10px 18px;
            border-radius: 8px;
            border: none;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}
        .btn-nav {{
            background: #e2e8f0;
            color: var(--text-main);
        }}
        .btn-nav:hover:not(:disabled) {{
            background: #cbd5e1;
        }}
        .btn-play {{
            background: var(--primary);
            color: #ffffff;
            min-width: 110px;
        }}
        .btn-play:hover {{
            background: #3730a3;
        }}
    </style>
</head>
<body>
    <div class="lab-container">
        <h1>{spec.title}</h1>

        <div class="progress-wrapper">
            <div class="progress-meta">
                <span id="step-counter">{step_word} 1 {of_word} {len(spec.steps)}</span>
                <span id="progress-pct">0%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" id="progress-fill"></div>
            </div>
        </div>

        <div class="step-card" id="step-card">
            <div class="step-label" id="step-label"></div>
            <div class="step-desc" id="step-desc"></div>
        </div>

        <div class="state-container">
            <div class="state-header">{state_label}</div>
            <div id="state-visual"></div>
        </div>

        <div class="controls-row">
            <button class="btn btn-nav" id="btn-prev" onclick="prevStep()">{prev_label}</button>
            <button class="btn btn-play" id="btn-play" onclick="togglePlay()">{play_label}</button>
            <button class="btn btn-nav" id="btn-next" onclick="nextStep()">{next_label}</button>
        </div>
    </div>

    <script>
        const steps = {steps_json};
        const total = steps.length;
        let currentIdx = 0;
        let timer = null;
        let isPlaying = false;

        const playText = "{play_label}";
        const pauseText = "{pause_label}";
        const stepWord = "{step_word}";
        const ofWord = "{of_word}";

        function renderCurrentStep() {{
            const step = steps[currentIdx];
            const card = document.getElementById('step-card');
            card.style.opacity = '0.5';

            setTimeout(() => {{
                document.getElementById('step-label').textContent = step.label || '';
                document.getElementById('step-desc').textContent = step.description || '';
                card.style.opacity = '1';
            }}, 100);

            // Progress & Counter
            const pct = Math.round(((currentIdx + 1) / total) * 100);
            document.getElementById('progress-fill').style.width = pct + '%';
            document.getElementById('progress-pct').textContent = pct + '%';
            document.getElementById('step-counter').textContent = stepWord + ' ' + (currentIdx + 1) + ' ' + ofWord + ' ' + total;

            // Nav buttons state
            document.getElementById('btn-prev').disabled = (currentIdx === 0);
            document.getElementById('btn-next').disabled = (currentIdx === total - 1);

            // Render State Visual
            renderState(step.state || {{}});
        }}

        function renderState(state) {{
            const container = document.getElementById('state-visual');
            container.innerHTML = '';

            // 1. Array representation if present
            if (Array.isArray(state.array)) {{
                const arrDiv = document.createElement('div');
                arrDiv.className = 'array-view';

                const low = typeof state.low === 'number' ? state.low : -1;
                const high = typeof state.high === 'number' ? state.high : 9999;
                const mid = typeof state.mid === 'number' ? state.mid : -1;
                const pointer = typeof state.pointer === 'number' ? state.pointer : -1;
                const found = typeof state.found === 'number' ? state.found : -1;

                state.array.forEach((val, i) => {{
                    const box = document.createElement('div');
                    box.className = 'array-box';
                    box.textContent = val;

                    if (i === found) {{
                        box.classList.add('found');
                    }} else if (i === mid || i === pointer) {{
                        box.classList.add('highlight');
                    }} else if ((low !== -1 && i < low) || (high !== 9999 && i > high)) {{
                        box.classList.add('dimmed');
                    }}

                    arrDiv.appendChild(box);
                }});
                container.appendChild(arrDiv);
            }}

            // 2. Extra metadata tags
            const pillsDiv = document.createElement('div');
            pillsDiv.className = 'state-badges';
            for (const [k, v] of Object.entries(state)) {{
                if (k === 'array') continue;
                const pill = document.createElement('span');
                pill.className = 'state-pill';
                pill.textContent = k + ': ' + (typeof v === 'object' ? JSON.stringify(v) : v);
                pillsDiv.appendChild(pill);
            }}
            if (pillsDiv.children.length > 0) {{
                container.appendChild(pillsDiv);
            }}
        }}

        function prevStep() {{
            if (currentIdx > 0) {{
                currentIdx--;
                renderCurrentStep();
            }}
        }}

        function nextStep() {{
            if (currentIdx < total - 1) {{
                currentIdx++;
                renderCurrentStep();
            }} else if (isPlaying) {{
                togglePlay();
            }}
        }}

        function togglePlay() {{
            const btn = document.getElementById('btn-play');
            if (isPlaying) {{
                clearInterval(timer);
                isPlaying = false;
                btn.textContent = playText;
            }} else {{
                if (currentIdx === total - 1) {{
                    currentIdx = 0;
                    renderCurrentStep();
                }}
                isPlaying = true;
                btn.textContent = pauseText;
                timer = setInterval(() => {{
                    if (currentIdx < total - 1) {{
                        nextStep();
                    }} else {{
                        togglePlay();
                    }}
                }}, 1500);
            }}
        }}

        // Initialize on load
        renderCurrentStep();
    </script>
</body>
</html>"""
    return html
