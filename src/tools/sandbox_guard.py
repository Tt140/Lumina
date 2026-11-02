"""LuminaLab Swarm - Sandbox Guard Verification Tool."""

import re
from src.contracts.schemas import VerifiedMicroLab, EngineType


def check_html_structure(html: str) -> list[str]:
    """Check for basic HTML5 document structure."""
    errors = []
    html_lower = html.lower()

    if not re.search(r'<!doctype\s+html', html_lower):
        errors.append("Missing <!DOCTYPE html> declaration")
    if "<html" not in html_lower or "</html>" not in html_lower:
        errors.append("Missing <html> or </html> tags")
    if "<head" not in html_lower or "</head>" not in html_lower:
        errors.append("Missing <head> or </head> tags")
    if "<body" not in html_lower or "</body>" not in html_lower:
        errors.append("Missing <body> or </body> tags")

    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    if not title_match or not title_match.group(1).strip():
        errors.append("Missing or empty <title> tag")

    return errors


def check_interactivity(html: str) -> list[str]:
    """Check for the presence of interactive elements or event handlers."""
    errors = []
    html_lower = html.lower()

    has_interactive = any(token in html_lower for token in [
        "<input", "<button", "onclick=", "oninput=", "addeventlistener"
    ])
    if not has_interactive:
        errors.append("No interactive elements found")

    return errors


def check_size_limit(html: str, max_kb: float = 200.0) -> list[str]:
    """Check that HTML UTF-8 byte size is within the allowed limit."""
    errors = []
    size_kb = len(html.encode('utf-8')) / 1024.0
    if size_kb > max_kb:
        errors.append(f"HTML size {size_kb:.1f}KB exceeds limit {max_kb:.1f}KB")
    return errors


def check_no_external_deps(html: str) -> list[str]:
    """Check that no external CDN, script, link, iframe, SVG remote asset, or @import is loaded."""
    errors = []
    if re.search(r'<script[^>]+src=\s*["\']?https?://', html, re.IGNORECASE):
        errors.append("External script dependency detected")
    if re.search(r'<link[^>]+href=\s*["\']?https?://', html, re.IGNORECASE):
        errors.append("External stylesheet/resource link detected")
    if re.search(r'<iframe', html, re.IGNORECASE):
        errors.append("Embedded iframe tag detected")
    if re.search(r'<(?:image|use)[^>]+(?:href|xlink:href)=\s*["\']?https?://', html, re.IGNORECASE):
        errors.append("External SVG resource dependency detected")
    if re.search(r'@import\s+(?:url\s*\()?\s*["\']?https?://', html, re.IGNORECASE):
        errors.append("External CSS @import dependency detected")
    return errors


def check_js_safety(html: str) -> list[str]:
    """Check for dangerous JavaScript patterns (cookie theft, unauthorized network calls)."""
    errors = []
    if re.search(r'\bdocument\.cookie\b', html):
        errors.append("Forbidden JS pattern: document.cookie")
    if re.search(r'\bwindow\.location\s*=', html):
        errors.append("Forbidden JS pattern: window.location =")
    if re.search(r'\bfetch\s*\(', html):
        errors.append("Forbidden JS network call: fetch()")
    if re.search(r'\bXMLHttpRequest\b', html):
        errors.append("Forbidden JS network call: XMLHttpRequest")
    if re.search(r'\bWebSocket\b', html):
        errors.append("Forbidden JS network call: WebSocket")
    if re.search(r'\bnavigator\.sendBeacon\b', html):
        errors.append("Forbidden JS network call: navigator.sendBeacon")
    return errors


def check_numerical_and_slider_integrity(html: str) -> list[str]:
    """Check that rendered values and slider ranges have numerical integrity."""
    errors = []
    # Check for unformatted JS or broken numerical artifacts rendered in DOM elements
    if re.search(r'>\s*(?:NaN|undefined|null|\[object Object\])\s*<', html):
        errors.append("Invalid numerical artifact (NaN/undefined/null) rendered in HTML")

    # Check for degenerate range inputs where min >= max
    for m in re.finditer(r'<input[^>]+type=["\']range["\'][^>]*>', html, re.IGNORECASE):
        tag = m.group(0)
        min_m = re.search(r'min=["\']([0-9.eE+-]+)["\']', tag)
        max_m = re.search(r'max=["\']([0-9.eE+-]+)["\']', tag)
        if min_m and max_m:
            try:
                min_v = float(min_m.group(1))
                max_v = float(max_m.group(1))
                if min_v >= max_v:
                    errors.append(f"Degenerate slider range: min ({min_v}) >= max ({max_v})")
            except ValueError:
                pass

        if not any(attr in tag.lower() for attr in ["oninput=", "onchange=", "data-idx="]):
            errors.append("Unbound slider input detected without event handler")

    return errors


def verify_micro_lab(html_content: str, engine_type: EngineType, max_kb: float = 200.0) -> VerifiedMicroLab:
    """
    Verifies interactive HTML against all quality, interactivity, and security checks.

    Does not raise exceptions; returns VerifiedMicroLab with passed_sandbox_guard
    and error_log populated.
    """
    errors = []
    errors.extend(check_html_structure(html_content))
    errors.extend(check_interactivity(html_content))
    errors.extend(check_size_limit(html_content, max_kb=max_kb))
    errors.extend(check_no_external_deps(html_content))
    errors.extend(check_js_safety(html_content))
    errors.extend(check_numerical_and_slider_integrity(html_content))

    passed = (len(errors) == 0)

    return VerifiedMicroLab(
        html_content=html_content,
        engine_type=engine_type,
        size_kb=0.0,  # Schema validator automatically computes size_kb
        passed_sandbox_guard=passed,
        error_log=errors,
        repair_attempts=0
    )
