// ============================================================
// LuminaLab Swarm — Offline In-App Runtime Viewer
// Unified Tabbed Navigation: [ Simulation Lab | Sensory | Mastery | Impact ]
// ============================================================

function launchVaultLab(labId) {
  let lab = CORE_LABS.find(l => l.id === labId);
  if (!lab) {
    const saved = getStoredVault();
    lab = saved.find(l => l.id === labId);
  }
  if (!lab) return;

  activeRuntimeLab = lab;
  const isAr = (currentLang === "ar");

  // Construct normalized payload for the 4 primary views
  const data = {
    id: lab.id,
    topic: isAr ? (lab.titleAr || lab.titleEn) : lab.titleEn,
    titleEn: lab.titleEn,
    titleAr: lab.titleAr,
    subjectEn: lab.subjectEn,
    subjectAr: lab.subjectAr,
    gradeEn: lab.gradeEn,
    gradeAr: lab.gradeAr,
    formula: lab.formula || "",
    simulation_spec: lab.simulation_spec || null,
    deconstructed: lab.deconstructed || null,
    verified_lab: {
      title: isAr ? (lab.titleAr || lab.titleEn) : lab.titleEn,
      formula: lab.formula || "",
      html_content: typeof lab.getHtml === "function" ? lab.getHtml(isAr) : (lab.html || lab.html_content || "")
    },
    accessibility: lab.accessibility || {
      adhd_steps: lab.adhd_steps || [],
      bionic_reading_html: isAr ? (lab.descAr || "") : (lab.descEn || ""),
      home_experiment: lab.home_experiment || null
    },
    challenge: lab.challenge || {
      challenge_question: isAr ? (lab.qAr || lab.challenge_question) : (lab.qEn || lab.challenge_question),
      challenge_hint: isAr ? (lab.hAr || lab.challenge_hint) : (lab.hEn || lab.challenge_hint),
      challenge_answer: isAr ? (lab.aAr || lab.challenge_answer) : (lab.aEn || lab.challenge_answer)
    },
    mastery: lab.mastery || lab.mastery_voice || lab.audio || {},
    audio: lab.audio || {
      audio_url: lab.audio_url || (lab.audio_file ? `/static/assets/audio/${lab.audio_file}` : null),
      script_text: isAr ? (lab.summaryAr || lab.descAr || "") : (lab.summaryEn || lab.descEn || "")
    },
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
  switchView("vault");
}

function downloadRuntimeLab() {
  downloadLab();
}

// Backward compatibility stub methods
function loadRuntimeLabContent(lab) {}
function populateRuntimeSensory(lab, isAr) {}
function populateRuntimeSocratic(lab, isAr) {}
function switchRuntimeTab(tabKey) {}
function toggleRuntimeHint() {}
function toggleRuntimeAnswer() {}

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
