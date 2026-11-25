// ============================================================
// LuminaLab Swarm — Offline In-App Runtime Viewer
// Unified Tabbed Navigation: [ Simulation Lab | Sensory | Mastery | Impact ]
// ============================================================

function pickLocalizedValue(val, isAr) {
  if (val && typeof val === "object" && !Array.isArray(val) && ("en" in val || "ar" in val)) {
    return isAr ? (val.ar !== undefined ? val.ar : val.en) : (val.en !== undefined ? val.en : val.ar);
  }
  return val;
}

function normalizeAdhdSteps(rawSteps, isAr) {
  const picked = pickLocalizedValue(rawSteps, isAr);
  if (!Array.isArray(picked)) return [];
  return picked.map((st, idx) => {
    if (typeof st === "string") return st;
    if (st && typeof st === "object") {
      return {
        title: st.title || st.step_title || `Step ${idx + 1}`,
        description: st.description || st.step_description || st.desc || ""
      };
    }
    return { title: `Step ${idx + 1}`, description: String(st || "") };
  });
}

function launchVaultLab(labId) {
  let lab = CORE_LABS.find(l => l.id === labId);
  if (!lab) {
    const saved = getStoredVault();
    lab = saved.find(l => l.id === labId);
  }
  if (!lab) return;

  activeRuntimeLab = lab;
  window.activeRuntimeLab = lab;
  const isAr = (currentLang === "ar");

  const rawAcc = lab.accessibility || lab.sensory_suite || {};
  const rawSteps = rawAcc.adhd_steps !== undefined ? rawAcc.adhd_steps : (lab.adhd_steps || []);
  const normalizedSteps = normalizeAdhdSteps(rawSteps, isAr);
  const bionicHtml = rawAcc.bionic_reading_html
    || pickLocalizedValue(rawAcc.bionic, isAr)
    || (isAr ? (lab.descAr || "") : (lab.descEn || ""));
  const kitchenText = rawAcc.kitchen_lab || pickLocalizedValue(rawAcc.kitchen, isAr) || "";
  const voiceScript = pickLocalizedValue(rawAcc.voice_script, isAr)
    || rawAcc.voice_script_text
    || (lab.audio && lab.audio.script_text)
    || (isAr ? (lab.summaryAr || lab.descAr || "") : (lab.summaryEn || lab.descEn || ""));
  const voiceAudioUrl = pickLocalizedValue(rawAcc.audio_url, isAr)
    || rawAcc.voice_audio_url
    || (rawAcc.voice_audio && rawAcc.voice_audio.audio_url)
    || lab.polly_audio_url
    || lab.audio_url
    || (lab.audio && lab.audio.audio_url)
    || (lab.audio_file ? `/static/assets/audio/${lab.audio_file}` : "");

  const rawCh = lab.challenge || lab.socratic_challenge || {};
  const normalizedChallenge = {
    challenge_question: rawCh.challenge_question || rawCh.question || (isAr ? (rawCh.qAr || lab.qAr || "") : (rawCh.qEn || lab.qEn || "")),
    challenge_hint: rawCh.challenge_hint || rawCh.hint || (isAr ? (rawCh.hAr || lab.hAr || "") : (rawCh.hEn || lab.hEn || "")),
    challenge_answer: rawCh.challenge_answer || rawCh.expected_answer || rawCh.model_answer || rawCh.challenge_solution || (isAr ? (rawCh.aAr || lab.aAr || "") : (rawCh.aEn || lab.aEn || ""))
  };

  // Construct normalized payload for the 4 primary views
  const data = {
    id: lab.id,
    isCore: Boolean(lab.isCore),
    topic: isAr ? (lab.titleAr || lab.titleEn) : lab.titleEn,
    titleEn: lab.titleEn,
    titleAr: lab.titleAr,
    subjectEn: lab.subjectEn,
    subjectAr: lab.subjectAr,
    gradeEn: lab.gradeEn,
    gradeAr: lab.gradeAr,
    descEn: lab.descEn,
    descAr: lab.descAr,
    engine: lab.engine || "SANDBOXED ENGINE",
    formula: lab.formula || "",
    getHtml: lab.getHtml,
    simulation_spec: lab.simulation_spec || null,
    deconstructed: lab.deconstructed || null,
    verified_lab: {
      title: isAr ? (lab.titleAr || lab.titleEn) : lab.titleEn,
      formula: lab.formula || "",
      html_content: typeof lab.getHtml === "function" ? lab.getHtml(isAr) : (lab.html || lab.html_content || "")
    },
    accessibility: {
      adhd_steps: normalizedSteps,
      bionic_reading_html: bionicHtml,
      home_experiment: rawAcc.home_experiment || lab.home_experiment || null,
      kitchen_lab: kitchenText,
      voice_script: voiceScript,
      voice_audio_url: voiceAudioUrl
    },
    challenge: normalizedChallenge,
    mastery: lab.mastery || lab.mastery_voice || lab.audio || {},
    audio: lab.audio || {
      audio_url: voiceAudioUrl || null,
      script_text: voiceScript
    },
    polly_audio_url: voiceAudioUrl || "",
    impact: lab.impact || {
      audit_id: lab.audit_id || `LL-VAULT-${lab.id}`,
      cryptographic_hash: lab.sha256 || "3f2e1a89b7c6d5e4a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4",
      pedagogy_score: 95
    }
  };

  setLastServerData(data);
  populateGeneratedOutputs(data);

  // Set mode to offline and activate tabbed navigation
  switchMode("offline");
  switchView("lab");

  showToast(isAr ? `تم فتح ${data.topic} بالمعاينة الكاملة` : `Opened ${data.topic} in Full Multi-Tab View`);
}

function closeRuntimePlayer() {
  activeRuntimeLab = null;
  window.activeRuntimeLab = null;
  switchView("vault");
}

function downloadRuntimeLab() {
  downloadLab();
}

// Backward compatibility & live language re-render support
function loadRuntimeLabContent(lab) {
  if (lab && lab.id && (currentView === "lab" || currentView === "sensory" || currentView === "mastery")) {
    const prevView = currentView;
    launchVaultLab(lab.id);
    if (prevView !== "lab") switchView(prevView);
  }
}
function populateRuntimeSensory(lab, isAr) {}
function populateRuntimeSocratic(lab, isAr) {}
function switchRuntimeTab(tabKey) {}
function toggleRuntimeHint() {}
function toggleRuntimeAnswer() {}

window.pickLocalizedValue = pickLocalizedValue;
window.activeRuntimeLab = (typeof activeRuntimeLab !== "undefined" ? activeRuntimeLab : null);
window.launchVaultLab = launchVaultLab;
window.closeRuntimePlayer = closeRuntimePlayer;
window.downloadRuntimeLab = downloadRuntimeLab;
window.loadRuntimeLabContent = loadRuntimeLabContent;
window.populateRuntimeSensory = populateRuntimeSensory;
window.populateRuntimeSocratic = populateRuntimeSocratic;
window.switchRuntimeTab = switchRuntimeTab;
window.toggleRuntimeHint = toggleRuntimeHint;
window.toggleRuntimeAnswer = toggleRuntimeAnswer;
