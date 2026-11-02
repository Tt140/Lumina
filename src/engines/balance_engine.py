"""LuminaLab Swarm - Universal Balance & Categorization Engine (HTML5/Interactive Cards)."""

import json
from src.contracts.schemas import SimulationSpec, EngineType


def _is_arabic(text: str) -> bool:
    """Check if the text contains Arabic characters."""
    return any('\u0600' <= ch <= '\u06FF' for ch in text)


def render_balance_lab(spec: SimulationSpec) -> str:
    """
    Renders an interactive balance and categorization micro-lab.

    Parameters:
        spec: SimulationSpec with engine_type=EngineType.BALANCE.

    Returns:
        A self-contained HTML5 string (<25KB) with inline CSS and JS.

    Raises:
        ValueError: If engine_type is not BALANCE or challenge_items has fewer than 2 items.
    """
    if spec.engine_type != EngineType.BALANCE:
        raise ValueError("Expected BALANCE engine type")

    if not spec.challenge_items or len(spec.challenge_items) < 2:
        raise ValueError("BALANCE engine requires at least two challenge items")

    # Detect language direction
    is_ar = _is_arabic(spec.title) or any(_is_arabic(item.get("label", "")) for item in spec.challenge_items)
    direction = "rtl" if is_ar else "ltr"
    lang = "ar" if is_ar else "en"

    # Extract distinct categories
    categories = list(dict.fromkeys(item.get("category", "General") for item in spec.challenge_items))

    # Localization labels
    bank_title = "بنك العناصر (انقر للاختيار ثم انقر على الفئة المناسبة)" if is_ar else "Item Bank (Click to select, then click a category zone)"
    check_btn_text = "تحقق ✓" if is_ar else "Check ✓"
    reset_btn_text = "حاول مرة أخرى 🔄" if is_ar else "Try Again 🔄"
    empty_zone_text = "اسحب أو انقر لوضع العناصر هنا" if is_ar else "Click here to place selected item"

    # Format category zones HTML
    zones_html = []
    for cat in categories:
        zone = f"""
        <div class="drop-zone" id="zone-{cat}" data-category="{cat}" onclick="placeSelectedItem('{cat}')">
            <div class="zone-header">{cat}</div>
            <div class="zone-content" id="zone-content-{cat}">
                <div class="zone-placeholder">{empty_zone_text}</div>
            </div>
        </div>
        """
        zones_html.append(zone)

    zones_rendered = "\n".join(zones_html)

    # Format items in bank HTML
    items_html = []
    for item in spec.challenge_items:
        iid = item.get("id")
        lbl = item.get("label", iid)
        card = f"""
        <div class="item-card" id="item-{iid}" data-id="{iid}" onclick="selectItem(event, '{iid}')">
            {lbl}
        </div>
        """
        items_html.append(card)

    bank_rendered = "\n".join(items_html)
    items_json = json.dumps(spec.challenge_items, ensure_ascii=False)

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
            --primary: #0284c7;
            --primary-light: #e0f2fe;
            --success: #16a34a;
            --success-light: #dcfce7;
            --danger: #dc2626;
            --danger-light: #fee2e2;
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
        .bank-container {{
            background: #f1f5f9;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
            border: 1px solid #cbd5e1;
        }}
        .bank-title {{
            font-size: 14px;
            font-weight: 700;
            color: var(--text-muted);
            margin-bottom: 12px;
            text-align: center;
        }}
        .items-pool {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            min-height: 48px;
        }}
        .item-card {{
            background: #ffffff;
            border: 2px solid #94a3b8;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .item-card:hover {{
            transform: translateY(-2px);
            border-color: var(--primary);
        }}
        .item-card.selected {{
            border-color: #f59e0b;
            background: #fef3c7;
            transform: scale(1.05);
            box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.35);
        }}
        .item-card.correct {{
            background: var(--success-light) !important;
            border-color: var(--success) !important;
            color: #14532d !important;
        }}
        .item-card.incorrect {{
            background: var(--danger-light) !important;
            border-color: var(--danger) !important;
            color: #7f1d1d !important;
        }}
        .zones-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        .drop-zone {{
            background: #ffffff;
            border: 2px dashed #94a3b8;
            border-radius: 12px;
            padding: 14px;
            min-height: 140px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .drop-zone:hover {{
            border-color: var(--primary);
            background: #f0f9ff;
        }}
        .zone-header {{
            font-size: 16px;
            font-weight: 700;
            color: var(--primary);
            text-align: center;
            padding-bottom: 8px;
            margin-bottom: 10px;
            border-bottom: 1px solid #e2e8f0;
        }}
        .zone-content {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-content: flex-start;
            min-height: 80px;
        }}
        .zone-placeholder {{
            width: 100%;
            text-align: center;
            font-size: 13px;
            color: #94a3b8;
            padding-top: 24px;
            pointer-events: none;
        }}
        .controls-row {{
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-bottom: 16px;
        }}
        .btn {{
            padding: 10px 22px;
            border-radius: 8px;
            border: none;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-check {{
            background: var(--success);
            color: #ffffff;
        }}
        .btn-check:hover {{
            background: #15803d;
        }}
        .btn-reset {{
            background: #e2e8f0;
            color: var(--text-main);
        }}
        .btn-reset:hover {{
            background: #cbd5e1;
        }}
        .feedback-banner {{
            padding: 14px;
            border-radius: 10px;
            text-align: center;
            font-weight: 700;
            display: none;
            animation: fadeIn 0.3s ease;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(-5px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .feedback-banner.success {{
            display: block;
            background: var(--success-light);
            color: #14532d;
            border: 1px solid #bbf7d0;
        }}
        .feedback-banner.partial {{
            display: block;
            background: #fef3c7;
            color: #92400e;
            border: 1px solid #fde68a;
        }}
    </style>
</head>
<body>
    <div class="lab-container">
        <h1>{spec.title}</h1>

        <div class="bank-container">
            <div class="bank-title">{bank_title}</div>
            <div class="items-pool" id="items-pool">
                {bank_rendered}
            </div>
        </div>

        <div class="zones-grid">
            {zones_rendered}
        </div>

        <div class="controls-row">
            <button class="btn btn-check" onclick="checkAnswers()">{check_btn_text}</button>
            <button class="btn btn-reset" onclick="resetItems()">{reset_btn_text}</button>
        </div>

        <div class="feedback-banner" id="feedback-banner"></div>
    </div>

    <script>
        const itemsData = {items_json};
        const itemMap = {{}};
        itemsData.forEach(item => {{ itemMap[item.id] = item; }});

        let selectedId = null;
        const itemPlacements = {{}}; // itemId -> category or null (in bank)

        const isArabic = "{lang}" === "ar";

        function selectItem(event, id) {{
            event.stopPropagation();
            clearFeedback();

            // If item already in a dropzone and clicked, send it back to bank
            if (itemPlacements[id]) {{
                moveItemToBank(id);
                return;
            }}

            if (selectedId === id) {{
                deselectAll();
            }} else {{
                deselectAll();
                selectedId = id;
                const el = document.getElementById('item-' + id);
                if (el) el.classList.add('selected');
            }}
        }}

        function deselectAll() {{
            selectedId = null;
            document.querySelectorAll('.item-card').forEach(el => {{
                el.classList.remove('selected');
            }});
        }}

        function placeSelectedItem(cat) {{
            if (!selectedId) return;
            clearFeedback();

            const card = document.getElementById('item-' + selectedId);
            const content = document.getElementById('zone-content-' + cat);

            if (card && content) {{
                // Hide placeholder
                const placeholder = content.querySelector('.zone-placeholder');
                if (placeholder) placeholder.style.display = 'none';

                content.appendChild(card);
                itemPlacements[selectedId] = cat;
                deselectAll();
            }}
        }}

        function moveItemToBank(id) {{
            const card = document.getElementById('item-' + id);
            const pool = document.getElementById('items-pool');
            const prevCat = itemPlacements[id];

            if (card && pool) {{
                pool.appendChild(card);
                itemPlacements[id] = null;
                card.classList.remove('correct', 'incorrect', 'selected');

                // Check if prev zone is empty
                if (prevCat) {{
                    const prevZone = document.getElementById('zone-content-' + prevCat);
                    if (prevZone && prevZone.querySelectorAll('.item-card').length === 0) {{
                        const placeholder = prevZone.querySelector('.zone-placeholder');
                        if (placeholder) placeholder.style.display = 'block';
                    }}
                }}
            }}
        }}

        function checkAnswers() {{
            let correctCount = 0;
            const total = itemsData.length;

            itemsData.forEach(item => {{
                const card = document.getElementById('item-' + item.id);
                const placedCat = itemPlacements[item.id];

                if (!card) return;

                card.classList.remove('correct', 'incorrect');
                if (placedCat === item.category) {{
                    card.classList.add('correct');
                    correctCount++;
                }} else {{
                    card.classList.add('incorrect');
                }}
            }});

            const banner = document.getElementById('feedback-banner');
            banner.className = 'feedback-banner';

            if (correctCount === total) {{
                banner.classList.add('success');
                banner.textContent = isArabic
                    ? `رائع ومبهر! أصبت ${{correctCount}} من ${{total}} إجابات صحيحة 🎉`
                    : `Awesome! You got ${{correctCount}} of ${{total}} correct! 🎉`;
            }} else {{
                banner.classList.add('partial');
                banner.textContent = isArabic
                    ? `أصبت ${{correctCount}} من ${{total}}. راجع العناصر باللون الأحمر وحاول مرة أخرى!`
                    : `You got ${{correctCount}} of ${{total}}. Check the red items and try again!`;
            }}
        }}

        function resetItems() {{
            itemsData.forEach(item => {{
                moveItemToBank(item.id);
            }});
            clearFeedback();
        }}

        function clearFeedback() {{
            const banner = document.getElementById('feedback-banner');
            banner.style.display = 'none';
            document.querySelectorAll('.item-card').forEach(c => {{
                c.classList.remove('correct', 'incorrect');
            }});
        }}
    </script>
</body>
</html>"""
    return html
