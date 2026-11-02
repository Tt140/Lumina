"""Phase 4 Offline Standalone Package & Vault Parity Test Suite."""

import json
import subprocess
import pytest
from pathlib import Path

from src.contracts.schemas import SimulationSpec, EngineType
from src.engines.slider_engine import render_slider_lab
from src.swarm.pair2_interactive import _sanitize_simulation_spec

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
STANDALONE_BUILDER_JS = WORKSPACE_ROOT / "src" / "ui" / "js" / "offline" / "standalone_builder.js"
VAULT_JS = WORKSPACE_ROOT / "src" / "ui" / "js" / "offline" / "vault.js"
OFFLINE_VIEWER_JS = WORKSPACE_ROOT / "src" / "ui" / "js" / "offline" / "offline_viewer.js"


def run_node_eval(script: str) -> dict:
    """Executes a JavaScript evaluation snippet using Node.js and returns parsed JSON output."""
    cmd = ["node", "-e", script]
    result = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Node execution failed (code {result.returncode}):\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    return json.loads(result.stdout)


# ============================================================================
# 1. Standalone Package Builder Parity Tests
# ============================================================================

def test_standalone_builder_generates_valid_4tab_package():
    """Verify buildStandaloneScenarioPackage produces a complete zero-CDN 4-tab HTML document."""
    node_script = f"""
    global.window = global;
    require("{STANDALONE_BUILDER_JS}");

    const mockScenario = {{
        titleEn: "Buffer Solutions & pH Balance",
        titleAr: "المحاليل المنظمة وتوازن الرقم الهيدروجيني",
        subjectEn: "Chemistry",
        subjectAr: "الكيمياء",
        gradeEn: "Grade 11",
        gradeAr: "الصف الحادي عشر",
        formula: "pH = pKa + log10([A⁻] / [HA])",
        verified_lab: {{
            title: "Buffer Solutions & pH Balance",
            formula: "pH = pKa + log10([A⁻] / [HA])",
            html_content: "<div id='sim'><h3>Buffer Chemistry Sandbox</h3></div>"
        }},
        accessibility: {{
            adhd_steps: [
                {{ title: "Step 1", description: "Observe acid" }},
                {{ title: "Step 2", description: "Add conjugate base" }},
                {{ title: "Step 3", description: "Measure pH response" }}
            ],
            bionic_reading_en: "<b>Buffers</b> <b>resist</b> <b>pH</b> <b>changes</b>."
        }},
        challenge: {{
            qEn: "What happens when strong acid is added to a buffer?",
            hEn: "The conjugate base neutralizes the added H+ ions.",
            aEn: "pH changes minimally due to neutralization by A-."
        }}
    }};

    const html = global.buildStandaloneScenarioPackage(mockScenario, false);
    const data = global.extractBilingualScenario(mockScenario, false);

    console.log(JSON.stringify({{
        hasDocType: html.includes("<!DOCTYPE html>"),
        hasSecLab: html.includes('id="sec-lab"'),
        hasSecSensory: html.includes('id="sec-sensory"'),
        hasSecMastery: html.includes('id="sec-mastery"'),
        hasSecImpact: html.includes('id="sec-impact"'),
        hasSimFrame: html.includes('id="sim-frame"'),
        hasLabHtmlEn: Boolean(data.labHtmlEn),
        hasLabHtmlAr: Boolean(data.labHtmlAr),
        formula: data.formula,
        htmlLength: html.length
    }}));
    """
    res = run_node_eval(node_script)
    assert res["hasDocType"] is True
    assert res["hasSecLab"] is True
    assert res["hasSecSensory"] is True
    assert res["hasSecMastery"] is True
    assert res["hasSecImpact"] is True
    assert res["hasSimFrame"] is True
    assert res["hasLabHtmlEn"] is True
    assert res["hasLabHtmlAr"] is True
    assert "pH = pKa" in res["formula"]
    assert res["htmlLength"] > 1000


def test_standalone_builder_bilingual_simulation_toggle():
    """Verify standalone builder preserves and switches between English and Arabic simulation HTML."""
    node_script = f"""
    global.window = global;
    require("{STANDALONE_BUILDER_JS}");

    const mockLab = {{
        titleEn: "Ohm Circuit",
        titleAr: "معمل أوم",
        getHtml: function(isAr) {{
            return isAr ? "<div id='sim'>تيار كهربائي</div>" : "<div id='sim'>Electric Current</div>";
        }}
    }};

    const extracted = global.extractBilingualScenario(mockLab, false);
    const standaloneHtml = global.buildStandaloneScenarioPackage(mockLab, false);

    console.log(JSON.stringify({{
        enSim: extracted.labHtmlEn,
        arSim: extracted.labHtmlAr,
        containsEnSim: standaloneHtml.includes("Electric Current"),
        containsArSim: standaloneHtml.includes("تيار كهربائي")
    }}));
    """
    res = run_node_eval(node_script)
    assert "Electric Current" in res["enSim"]
    assert "تيار كهربائي" in res["arSim"]
    # Standalone JSON data includes both bilingual simulations
    assert res["containsEnSim"] is True
    assert res["containsArSim"] is True


def test_standalone_builder_prevents_script_tag_truncation():
    """Verify that embedded <script> tags inside labHtml are safely escaped as \\u003c

    This prevents premature </script> termination in browser HTML parsers (OWASP standard).
    """
    node_script = f"""
    global.window = global;
    require("{STANDALONE_BUILDER_JS}");

    const mockLab = {{
        titleEn: "Bacterial Binary Fission",
        titleAr: "الانشطار الثنائي للبكتيريا",
        html_content: "<div id='sim'><script>const count = 1000; console.log('done');</" + "script></div>"
    }};

    const standaloneHtml = global.buildStandaloneScenarioPackage(mockLab, false);

    // Extract raw payload inside <script id="scenario-data" type="application/json">...</script>
    const match = standaloneHtml.match(/<script id="scenario-data" type="application\\/json">([\\s\\S]*?)<\\/script>/);
    if (!match) {{
        console.log(JSON.stringify({{ error: "Script tag missing" }}));
        process.exit(0);
    }}

    const innerJson = match[1];
    const hasPrematureClosingTag = innerJson.includes("</script>");
    let parsedCleanly = false;
    let labHtmlMatch = false;

    try {{
        const parsed = JSON.parse(innerJson);
        parsedCleanly = true;
        labHtmlMatch = parsed.labHtmlEn.includes("<script>const count = 1000;");
    }} catch (e) {{
        parsedCleanly = false;
    }}

    console.log(JSON.stringify({{
        hasPrematureClosingTag: hasPrematureClosingTag,
        parsedCleanly: parsedCleanly,
        labHtmlMatch: labHtmlMatch,
        escapedScriptFound: innerJson.includes("\\\\u003cscript")
    }}));
    """
    res = run_node_eval(node_script)
    assert res["hasPrematureClosingTag"] is False
    assert res["parsedCleanly"] is True
    assert res["labHtmlMatch"] is True
    assert res["escapedScriptFound"] is True


def test_app_js_standalone_builder_prevents_script_tag_truncation():
    """Verify src/ui/app.js has matching OWASP sanitization for standalone lab export."""
    app_js_path = WORKSPACE_ROOT / "src" / "ui" / "app.js"
    node_script = f"""
    global.window = global;
    global.document = {{ addEventListener: () => {{}} }};
    global.localStorage = {{ getItem: () => null, setItem: () => {{}} }};
    global.$ = () => null;
    require("{app_js_path}");

    const mockLab = {{
        titleEn: "Bacterial Binary Fission",
        titleAr: "الانشطار الثنائي للبكتيريا",
        html_content: "<div id='sim'><script>const count = 2000; console.log('test');</" + "script></div>"
    }};

    const standaloneHtml = global.buildStandaloneScenarioPackage(mockLab, false);
    const match = standaloneHtml.match(/<script id="scenario-data" type="application\\/json">([\\s\\S]*?)<\\/script>/);
    const innerJson = match ? match[1] : "";
    const hasPremature = innerJson.includes("</script>");
    const parsed = JSON.parse(innerJson);

    console.log(JSON.stringify({{
        hasPremature: hasPremature,
        restoredHtml: parsed.labHtmlEn.includes("<script>const count = 2000;"),
        hasEscaped: innerJson.includes("\\\\u003cscript")
    }}));
    """
    res = run_node_eval(node_script)
    assert res["hasPremature"] is False
    assert res["restoredHtml"] is True
    assert res["hasEscaped"] is True


# ============================================================================
# 2. Offline Vault Parity & Auto-Healing Tests
# ============================================================================

def test_vault_auto_heals_legacy_ph_bounds():
    """Verify getStoredVault automatically heals legacy pH labs that had boundMax = 100.0."""
    node_script = f"""
    global.window = global;
    global.$ = () => null;
    global.CORE_LABS = [];

    const mockStorage = {{}};
    global.localStorage = {{
        getItem: (k) => mockStorage[k] || null,
        setItem: (k, v) => {{ mockStorage[k] = v; }}
    }};

    // Inject legacy unhealed item with boundMax = 100.0 and isLogScale = true
    const legacyItem = {{
        id: "saved_legacy_buffer",
        titleEn: "Buffer Solution and Henderson Hasselbalch",
        titleAr: "المحلول المنظم",
        descEn: "Saved from Live Cloud Studio",
        formula: "pH = pKa + log10([A⁻] / [HA])",
        html: "<html><body><script>let boundMin = 0.0; let boundMax = 100.0; const isLogScale = true;</script></body></html>",
        simulation_spec: {{
            title: "Buffer Solution",
            formula_expression: "pH = pKa + log10([A⁻] / [HA])",
            result_symbol: "Result",
            result_min: 0.0,
            result_max: 100.0,
            is_logarithmic_output: true
        }}
    }};

    mockStorage["lumina_offline_vault"] = JSON.stringify([legacyItem]);

    require("{VAULT_JS}");
    const healedList = global.getStoredVault();
    const healed = healedList[0];

    console.log(JSON.stringify({{
        htmlContains14: healed.html.includes("let boundMax = 14.0;"),
        htmlNotContains100: !healed.html.includes("boundMax = 100.0"),
        htmlIsLogFalse: healed.html.includes("const isLogScale = false;"),
        specResultMax: healed.simulation_spec.result_max,
        specResultMin: healed.simulation_spec.result_min,
        specResultSymbol: healed.simulation_spec.result_symbol,
        specIsLog: healed.simulation_spec.is_logarithmic_output,
        descHealed: !healed.descEn.includes("Saved from Live Cloud Studio")
    }}));
    """
    res = run_node_eval(node_script)
    assert res["htmlContains14"] is True
    assert res["htmlNotContains100"] is True
    assert res["htmlIsLogFalse"] is True
    assert res["specResultMax"] == 14.0
    assert res["specResultMin"] == 0.0
    assert res["specResultSymbol"] == "pH"
    assert res["specIsLog"] is False
    assert res["descHealed"] is True


def test_vault_auto_heals_legacy_lever_spec():
    """Verify getStoredVault automatically heals mechanical lever specifications to Balance."""
    node_script = f"""
    global.window = global;
    global.$ = () => null;
    global.CORE_LABS = [];

    const mockStorage = {{}};
    global.localStorage = {{
        getItem: (k) => mockStorage[k] || null,
        setItem: (k, v) => {{ mockStorage[k] = v; }}
    }};

    const legacyLever = {{
        id: "saved_legacy_lever",
        titleEn: "Physics Lever Balance",
        titleAr: "الروافع والاتزان",
        descEn: "Investigate lever arms.",
        formula: "Balance = Effort * Arm",
        html: "<html><body>Lever</body></html>",
        simulation_spec: {{
            title: "Lever Balance",
            result_symbol: "Result",
            result_min: 0.0,
            result_max: 100.0
        }}
    }};

    mockStorage["lumina_offline_vault"] = JSON.stringify([legacyLever]);

    require("{VAULT_JS}");
    const healedList = global.getStoredVault();
    const healed = healedList[0];

    console.log(JSON.stringify({{
        resultSymbol: healed.simulation_spec.result_symbol,
        resultMin: healed.simulation_spec.result_min,
        resultMax: healed.simulation_spec.result_max
    }}));
    """
    res = run_node_eval(node_script)
    assert res["resultSymbol"] == "Balance"
    assert res["resultMin"] == 0.0
    assert res["resultMax"] == 100.0


# ============================================================================
# 3. Offline In-App Viewer Parity Tests
# ============================================================================

def test_offline_viewer_launch_preserves_contract_fields():
    """Verify launchVaultLab passes simulation_spec, deconstructed, and mastery into lastServerData."""
    node_script = f"""
    global.window = global;
    let capturedServerData = null;

    global.setLastServerData = (data) => {{ capturedServerData = data; }};
    global.populateGeneratedOutputs = () => {{}};
    global.switchMode = () => {{}};
    global.switchView = () => {{}};
    global.showToast = () => {{}};
    global.currentLang = "en";

    const mockLab = {{
        id: "vault_buffer_1",
        titleEn: "Buffer Solution",
        titleAr: "محلول منظم",
        subjectEn: "Chemistry",
        subjectAr: "الكيمياء",
        gradeEn: "Grade 11",
        gradeAr: "الصف 11",
        formula: "pH = pKa + log10([A⁻] / [HA])",
        html: "<html><body>Buffer Lab</body></html>",
        simulation_spec: {{
            result_symbol: "pH",
            result_min: 0.0,
            result_max: 14.0,
            is_logarithmic_output: false
        }},
        deconstructed: {{
            core_concept: "Acid-base buffering",
            simplified_explanation: "Resists pH change"
        }},
        mastery: {{
            friendly_summary_en: "Buffers keep pH steady."
        }}
    }};

    global.CORE_LABS = [mockLab];
    global.getStoredVault = () => [];

    require("{OFFLINE_VIEWER_JS}");
    global.launchVaultLab("vault_buffer_1");

    console.log(JSON.stringify({{
        hasCaptured: Boolean(capturedServerData),
        hasSimulationSpec: Boolean(capturedServerData && capturedServerData.simulation_spec),
        specResultMax: capturedServerData.simulation_spec.result_max,
        hasDeconstructed: Boolean(capturedServerData && capturedServerData.deconstructed),
        hasMastery: Boolean(capturedServerData && capturedServerData.mastery),
        verifiedLabHtml: capturedServerData.verified_lab.html_content
    }}));
    """
    res = run_node_eval(node_script)
    assert res["hasCaptured"] is True
    assert res["hasSimulationSpec"] is True
    assert res["specResultMax"] == 14.0
    assert res["hasDeconstructed"] is True
    assert res["hasMastery"] is True
    assert "Buffer Lab" in res["verifiedLabHtml"]


# ============================================================================
# 4. Full Pipeline Integration: Engine -> Standalone Package Parity
# ============================================================================

def test_full_pipeline_engine_to_standalone_package():
    """Verify that a Python-generated chemistry lab embedded into a standalone package has 0..14 bounds."""
    spec_data = {
        "engine_type": EngineType.SLIDER,
        "title": "Henderson-Hasselbalch Buffer",
        "variables": [
            {"name": "pKa", "symbol": "pKa", "unit": "", "min_val": 3.0, "max_val": 10.0, "default_val": 4.76},
            {"name": "Conjugate Base", "symbol": "[A⁻]", "unit": "M", "min_val": 0.01, "max_val": 1.0, "default_val": 0.1},
            {"name": "Weak Acid", "symbol": "[HA]", "unit": "M", "min_val": 0.01, "max_val": 1.0, "default_val": 0.1}
        ],
        "formula_expression": "pH = pKa + log10([A⁻] / [HA])"
    }

    # 2. Apply scientific domain bounds guard via sanitizer
    spec_data = _sanitize_simulation_spec(spec_data)
    assert spec_data["result_symbol"] == "pH"
    assert spec_data["result_min"] == 0.0
    assert spec_data["result_max"] == 14.0
    assert spec_data["is_logarithmic_output"] is False

    spec = SimulationSpec(**spec_data)

    # 3. Render HTML via SliderEngine
    lab_html = render_slider_lab(spec)
    assert "boundMin = 0.0" in lab_html
    assert "boundMax = 14.0" in lab_html
    assert "isLogScale = false" in lab_html
    assert "getPhColor" in lab_html

    # 4. Pass into Standalone Builder via Node
    node_script = f"""
    global.window = global;
    require("{STANDALONE_BUILDER_JS}");

    const scenario = {{
        titleEn: "{spec.title}",
        titleAr: "معمل المحلول المنظم",
        subjectEn: "Chemistry",
        subjectAr: "الكيمياء",
        gradeEn: "Grade 11",
        gradeAr: "الصف 11",
        formula: "{spec.formula_expression}",
        verified_lab: {{
            title: "{spec.title}",
            formula: "{spec.formula_expression}",
            html_content: {json.dumps(lab_html)}
        }}
    }};

    const pkgHtml = global.buildStandaloneScenarioPackage(scenario, false);

    console.log(JSON.stringify({{
        containsBoundMin0: pkgHtml.includes("boundMin = 0.0"),
        containsBoundMax14: pkgHtml.includes("boundMax = 14.0"),
        containsIsLogFalse: pkgHtml.includes("isLogScale = false"),
        containsPhColorFunc: pkgHtml.includes("getPhColor"),
        pkgSizeKb: Math.round(pkgHtml.length / 1024)
    }}));
    """
    res = run_node_eval(node_script)
    assert res["containsBoundMin0"] is True
    assert res["containsBoundMax14"] is True
    assert res["containsIsLogFalse"] is True
    assert res["containsPhColorFunc"] is True
    # Verify package is lightweight (< 150 KB)
    assert res["pkgSizeKb"] < 150
