// ============================================================
// LuminaLab Swarm — Shared State & Core Controllers
// ============================================================

const $ = (id) => document.getElementById(id);
window.$ = $;

let currentMode = "online";
let currentView = "studio";
let currentLang = "en";
let lastServerData = null;
var isMockMode = true;
var activeRuntimeLab = null;

window.currentMode = currentMode;
window.currentView = currentView;
window.currentLang = currentLang;
window.lastServerData = lastServerData;
window.isMockMode = isMockMode;
window.activeRuntimeLab = activeRuntimeLab;
var currentVaultFilter = "all";
window.currentVaultFilter = currentVaultFilter;
window.getCurrentMode = () => currentMode;
window.getCurrentView = () => currentView;
window.getCurrentLang = () => currentLang;
window.getLastServerData = () => lastServerData;
window.setLastServerData = (data) => { lastServerData = data; };

// WORKFLOW & ENVIRONMENT MODE CONTROLLERS
// ============================================================
const ALL_VIEWS = ["studio", "lab", "sensory", "mastery", "impact", "vault"];
let lastOnlineView = "studio";

function switchMode(mode) {
  currentMode = mode;
  const isOnline = (mode === "online");

  if ($("btn-mode-online")) $("btn-mode-online").classList.toggle("active", isOnline);
  if ($("btn-mode-offline")) $("btn-mode-offline").classList.toggle("active", !isOnline);

  const tabStudio = $("tab-studio");
  const tabVault = $("tab-vault");
  if (tabStudio) tabStudio.style.display = isOnline ? "inline-flex" : "none";
  if (tabVault) tabVault.style.display = !isOnline ? "inline-flex" : "none";

  const subnav = $("subnav-bar");
  if (subnav) subnav.style.display = "flex";

  if (isOnline) {
    switchView(lastOnlineView || "studio");
  } else {
    if (activeRuntimeLab) {
      switchView("lab");
    } else {
      switchView("vault");
    }
  }
}

function switchView(viewName) {
  if (!ALL_VIEWS.includes(viewName)) viewName = "studio";
  currentView = viewName;
  const isVault = (viewName === "vault");

  const subnav = $("subnav-bar");
  if (subnav) subnav.style.display = "flex";

  if (!isVault && currentMode === "online") {
    lastOnlineView = viewName;
  }

  // Update tabs active state
  ALL_VIEWS.forEach(v => {
    const tab = $(`tab-${v}`);
    if (tab) tab.classList.toggle("active", v === viewName);
  });

  // Update view sections visibility
  ALL_VIEWS.forEach(v => {
    const sec = $(`view-${v}`);
    if (sec) sec.classList.toggle("active", v === viewName);
  });

  // If entering vault view, ensure cards are rendered
  if (viewName === "vault") {
    renderVaultGrid();
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// ============================================================

// LANGUAGE TOGGLE & LOCALIZATION
// ============================================================
function toggleLang() {
  currentLang = currentLang === "en" ? "ar" : "en";
  applyLang(currentLang);
}

function isSampleOrUntouched() {
  const sub = $("input-subject").value.trim();
  const top = $("input-topic").value.trim();
  const txt = $("input-text").value.trim();

  const isAr = (sub === "الفيزياء") && (top === "قانون أوم") && txt.startsWith("ينص قانون أوم");
  const isEn = (sub === "Physics") && (top === "Ohm's Law") && txt.startsWith("Ohm's law states");
  return isAr || isEn;
}

function applyLang(lang) {
  const t = I18N[lang];
  document.documentElement.lang = t.lang;
  document.documentElement.dir = t.dir;

  // Global Header
  document.title = t.pageTitle;
  $("btn-lang").textContent = t.langBtn;
  if ($("header-status-text")) {
    $("header-status-text").textContent = (typeof isMockMode !== "undefined" && isMockMode) ? t.statusMock : t.statusCloud;
  }

  // Primary Environment Mode Switcher Labels
  if ($("txt-mode-online")) $("txt-mode-online").textContent = t.modeOnline;
  if ($("txt-mode-offline")) $("txt-mode-offline").textContent = t.modeOffline;

  // Nav Tabs Labels
  if ($("tab-txt-studio")) $("tab-txt-studio").textContent = t.tabStudio;
  if ($("tab-txt-vault")) $("tab-txt-vault").textContent = t.tabVault || (lang === "ar" ? "مكتبة الخزنة" : "Vault Library");
  if ($("tab-txt-lab")) $("tab-txt-lab").textContent = t.tabLab;
  if ($("tab-txt-sensory")) $("tab-txt-sensory").textContent = t.tabSensory;
  if ($("tab-txt-mastery")) $("tab-txt-mastery").textContent = t.tabMastery;
  if ($("tab-txt-impact")) $("tab-txt-impact").textContent = t.tabImpact;

  // Banners
  if ($("txt-badge-online")) $("txt-badge-online").textContent = t.badgeOnline;
  if ($("txt-desc-online")) $("txt-desc-online").innerHTML = t.descOnline;
  if ($("txt-badge-offline")) $("txt-badge-offline").textContent = t.badgeOffline;
  if ($("txt-desc-offline")) $("txt-desc-offline").innerHTML = t.descOffline;

  // 1. Studio View
  if ($("hero-badge-studio")) $("hero-badge-studio").textContent = t.heroBadgeStudio;
  if ($("hero-title-studio")) $("hero-title-studio").innerHTML = t.heroTitleStudio;
  if ($("hero-sub-studio")) $("hero-sub-studio").textContent = t.heroSubStudio;
  if ($("studio-form-title")) $("studio-form-title").textContent = t.studioFormTitle;
  if ($("studio-form-sub")) $("studio-form-sub").textContent = t.studioFormSub;
  if ($("btn-txt-sample")) $("btn-txt-sample").textContent = t.btnSample;
  if ($("lbl-subject")) $("lbl-subject").textContent = t.lblSubject;
  if ($("lbl-grade")) $("lbl-grade").textContent = t.lblGrade;
  if ($("lbl-topic")) $("lbl-topic").textContent = t.lblTopic;
  if ($("lbl-text")) $("lbl-text").textContent = t.lblText;
  if ($("btn-txt-run")) $("btn-txt-run").textContent = t.btnRun;
  if ($("txt-guard-notice")) $("txt-guard-notice").textContent = t.guardNotice;
  if ($("pipeline-status-title")) $("pipeline-status-title").textContent = t.pipelineTitle;

  if (isSampleOrUntouched()) {
    if ($("input-subject")) $("input-subject").value = t.sampleSubject;
    if ($("input-topic")) $("input-topic").value = t.sampleTopic;
    if ($("input-text")) $("input-text").value = t.sampleText;
    if ($("txt-char-counter")) $("txt-char-counter").textContent = `${t.sampleText.length} ${t.charUnit}`;
  }

  const gradeSel = $("input-grade");
  if (gradeSel && t && t.grades) {
    const prevVal = gradeSel.value || "8";
    gradeSel.innerHTML = "";
    while (gradeSel.firstChild) {
      gradeSel.removeChild(gradeSel.firstChild);
    }
    t.grades.forEach(g => {
      const opt = document.createElement("option");
      opt.value = g.v;
      opt.textContent = g.l;
      if (g.v === prevVal) opt.selected = true;
      gradeSel.appendChild(opt);
    });
  }

  // 2. Lab Player View
  $("hero-badge-lab").textContent = t.heroBadgeLab;
  $("hero-title-lab").innerHTML = t.heroTitleLab;
  $("hero-sub-lab").textContent = t.heroSubLab;
  $("empty-lab-h").textContent = t.emptyLabH;
  $("empty-lab-p").textContent = t.emptyLabP;
  $("btn-txt-goto-studio").textContent = t.btnGotoStudio;
  $("btn-txt-reload-lab").textContent = t.btnReloadLab;
  $("btn-txt-save-vault").textContent = t.btnSaveVault;
  $("btn-txt-download").textContent = t.btnDownloadLab;
  $("save-toast").textContent = t.saveToast;

  // 3. Sensory View
  $("hero-badge-sensory").textContent = t.heroBadgeSensory;
  $("hero-title-sensory").innerHTML = t.heroTitleSensory;
  $("hero-sub-sensory").textContent = t.heroSubSensory;
  $("empty-sensory-h").textContent = t.emptySensoryH;
  $("empty-sensory-p").textContent = t.emptySensoryP;
  $("btn-txt-goto-studio-2").textContent = t.btnGotoStudio;
  $("sec-adhd-title").textContent = t.secAdhdTitle;
  $("sec-adhd-sub").textContent = t.secAdhdSub;
  $("sec-bionic-title").textContent = t.secBionicTitle;
  $("sec-bionic-sub").textContent = t.secBionicSub;
  $("sec-kitchen-title").textContent = t.secKitchenTitle;
  $("sec-kitchen-sub").textContent = t.secKitchenSub;

  // 4. Mastery View
  if ($("hero-badge-mastery")) $("hero-badge-mastery").textContent = t.heroBadgeMastery;
  if ($("hero-title-mastery")) $("hero-title-mastery").innerHTML = t.heroTitleMastery;
  if ($("hero-sub-mastery")) $("hero-sub-mastery").textContent = t.heroSubMastery;
  if ($("empty-mastery-h")) $("empty-mastery-h").textContent = t.emptyMasteryH;
  if ($("empty-mastery-p")) $("empty-mastery-p").textContent = t.emptyMasteryP;
  if ($("btn-txt-goto-studio-3")) $("btn-txt-goto-studio-3").textContent = t.btnGotoStudio;
  if ($("sec-voice-title")) $("sec-voice-title").textContent = t.secVoiceTitle;
  if ($("sec-voice-sub")) $("sec-voice-sub").textContent = t.secVoiceSub;
  if ($("btn-txt-download-audio")) $("btn-txt-download-audio").textContent = t.btnDownloadAudio;
  if ($("lbl-transcript-title")) $("lbl-transcript-title").textContent = t.lblTranscriptTitle;
  if (typeof updateVoiceBadge === "function") updateVoiceBadge();
  if ($("sec-socratic-title")) $("sec-socratic-title").textContent = t.secSocraticTitle;
  if ($("sec-socratic-sub")) $("sec-socratic-sub").textContent = t.secSocraticSub;
  if ($("socratic-prompt-badge")) $("socratic-prompt-badge").textContent = t.socraticPromptBadge;
  if ($("lbl-student-hypothesis")) $("lbl-student-hypothesis").textContent = t.lblHypothesis;
  if ($("input-student-answer")) $("input-student-answer").placeholder = t.hypothesisPh;
  if ($("btn-txt-check")) $("btn-txt-check").textContent = t.btnCheck;
  if ($("lbl-hint-badge")) $("lbl-hint-badge").textContent = t.lblHintBadge;
  if ($("lbl-answer-badge")) $("lbl-answer-badge").textContent = t.lblAnswerBadge;

  const hintPanel = $("hint-panel");
  const hintOpen = hintPanel && hintPanel.classList && hintPanel.classList.contains("open");
  if ($("btn-txt-hint")) $("btn-txt-hint").textContent = hintOpen ? t.btnHintHide : t.btnHintReveal;
  const ansPanel = $("answer-panel");
  const ansOpen = ansPanel && ansPanel.classList && ansPanel.classList.contains("open");
  if ($("btn-txt-answer")) $("btn-txt-answer").textContent = ansOpen ? t.btnAnswerHide : t.btnAnswerReveal;

  // 5. Impact View
  if ($("hero-badge-impact")) $("hero-badge-impact").textContent = t.heroBadgeImpact;
  if ($("hero-title-impact")) $("hero-title-impact").innerHTML = t.heroTitleImpact;
  if ($("hero-sub-impact")) $("hero-sub-impact").textContent = t.heroSubImpact;
  if ($("stat-lbl-grade")) $("stat-lbl-grade").textContent = t.statGrade;
  if ($("stat-lbl-cog")) $("stat-lbl-cog").textContent = t.statCog;
  if ($("stat-lbl-size")) $("stat-lbl-size").textContent = t.statSize;
  if ($("stat-lbl-offline")) $("stat-lbl-offline").textContent = t.statOffline;
  if ($("sec-cloud-stats-title")) $("sec-cloud-stats-title").textContent = t.secCloudStatsTitle;
  if ($("sec-cloud-stats-sub")) $("sec-cloud-stats-sub").textContent = t.secCloudStatsSub;
  if ($("btn-txt-refresh")) $("btn-txt-refresh").textContent = t.btnRefresh;
  if ($("lbl-audit-sessions")) $("lbl-audit-sessions").textContent = t.lblAuditSessions;
  if ($("lbl-audit-reduction")) $("lbl-audit-reduction").textContent = t.lblAuditReduction;
  if ($("lbl-audit-offline")) $("lbl-audit-offline").textContent = t.lblAuditOffline;

  // 6. Vault View
  if ($("hero-badge-vault")) $("hero-badge-vault").textContent = t.heroBadgeVault;
  if ($("hero-title-vault")) $("hero-title-vault").innerHTML = t.heroTitleVault;
  if ($("hero-sub-vault")) $("hero-sub-vault").textContent = t.heroSubVault;
  if ($("txt-filter-all")) $("txt-filter-all").textContent = t.txtFilterAll;
  if ($("txt-filter-core")) $("txt-filter-core").textContent = t.txtFilterCore;
  if ($("txt-filter-saved")) $("txt-filter-saved").textContent = t.txtFilterSaved;

  // Runtime View (if present)
  if ($("txt-back-vault")) $("txt-back-vault").textContent = t.txtBackVault;
  if ($("runtime-lab-badge")) $("runtime-lab-badge").textContent = t.runtimeBadge;
  if ($("btn-txt-download-runtime")) $("btn-txt-download-runtime").textContent = t.btnDownloadRuntime;
  if ($("txt-rt-adhd")) $("txt-rt-adhd").textContent = t.txtRtAdhd;
  if ($("txt-rt-bionic")) $("txt-rt-bionic").textContent = t.txtRtBionic;
  if ($("txt-rt-kitchen")) $("txt-rt-kitchen").textContent = t.txtRtKitchen;
  if ($("txt-rt-socratic")) $("txt-rt-socratic").textContent = t.txtRtSocratic;
  if ($("lbl-rt-hint-badge")) $("lbl-rt-hint-badge").textContent = t.lblRtHintBadge;
  if ($("lbl-rt-answer-badge")) $("lbl-rt-answer-badge").textContent = t.lblRtAnswerBadge;

  // Re-render dynamic components
  renderVaultGrid();
  if (activeRuntimeLab) {
    loadRuntimeLabContent(activeRuntimeLab);
  }

  // Synchronize Voice Companion with the selected language
  if (typeof populateVoiceCompanion === "function") {
    if (lastServerData && lastServerData.lesson_input && lastServerData.lesson_input.language === lang) {
      populateVoiceCompanion(lastServerData);
    } else if (activeRuntimeLab) {
      populateVoiceFromLab(activeRuntimeLab, lang === "ar");
    } else {
      populateVoiceCompanion(null);
    }
  }
}

function loadSampleData() {
  const t = I18N[currentLang];
  $("input-subject").value = t.sampleSubject;
  $("input-topic").value = t.sampleTopic;
  $("input-grade").value = t.sampleGrade;
  $("input-text").value = t.sampleText;
  $("txt-char-counter").textContent = `${t.sampleText.length} ${t.charUnit}`;
}

// ============================================================
// GLOBAL FLOATING TOAST NOTIFICATION
// ============================================================
function showToast(message, isError = false) {
  let toastEl = $("global-floating-toast");
  if (!toastEl) {
    toastEl = document.createElement("div");
    toastEl.id = "global-floating-toast";
    toastEl.style.cssText = "position:fixed; top:24px; left:50%; transform:translateX(-50%); z-index:99999; padding:12px 24px; border-radius:9999px; font-weight:700; font-size:13px; box-shadow:0 10px 25px -5px rgba(0,0,0,0.18); transition:all 0.3s cubic-bezier(0.16, 1, 0.3, 1); pointer-events:none; opacity:0;";
    document.body.appendChild(toastEl);
  }
  toastEl.textContent = message;
  toastEl.style.background = isError ? "#EF4444" : "#059669";
  toastEl.style.color = "#FFFFFF";
  toastEl.style.opacity = "1";
  toastEl.style.transform = "translateX(-50%) translateY(0)";

  clearTimeout(toastEl._timer);
  toastEl._timer = setTimeout(() => {
    toastEl.style.opacity = "0";
    toastEl.style.transform = "translateX(-50%) translateY(-10px)";
  }, 4500);
}

// ============================================================

window.currentMode = currentMode;
window.currentView = currentView;
window.currentLang = currentLang;
window.lastServerData = lastServerData;
window.ALL_VIEWS = ALL_VIEWS;
window.switchMode = switchMode;
window.switchView = switchView;
window.toggleLang = toggleLang;
window.applyLang = applyLang;
window.showToast = showToast;
window.isSampleOrUntouched = isSampleOrUntouched;
window.loadSampleData = loadSampleData;
