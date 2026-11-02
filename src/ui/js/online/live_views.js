// ============================================================
// LuminaLab Swarm — Online Live Views Renderer
// ============================================================
function formatArabicBionicPlain(text) {
  const punctRegex = /([.,!?;:،؟]+)$/;
  return text.split(/\s+/).map(word => {
    if (!word) return "";
    const m = punctRegex.exec(word);
    const punct = m ? m[1] : "";
    const core = punct ? word.slice(0, -punct.length) : word;
    if (core.length <= 2 || ARABIC_BIONIC_STOPS.has(core)) {
      return word;
    }
    return `<b>${core}</b>${punct}`;
  }).join(" ");
}

function sanitizeArabicBionic(html) {
  if (!html || typeof html !== "string") return html || "";
  if (!/[\u0600-\u06FF]/.test(html)) return html;

  // If raw text without <b> tags, apply semantic whole-word anchors
  if (!/<b[ >]/i.test(html)) {
    return formatArabicBionicPlain(html);
  }

  let healed = html;

  // 1. Heal tatweel/hyphen severed words: <b>العـ</b> لاقة or <b>العـ</b>لاقة
  healed = healed.replace(/<b>([\u0600-\u06FF]+)[\u0640\-]<\/b>\s*([\u0600-\u06FF]+)/g, "<b>$1$2</b>");

  // 2. Heal directly adjacent tags: <b>ين</b>ص
  healed = healed.replace(/<b>([\u0600-\u06FF]+)<\/b>([\u0600-\u06FF]+)/g, "<b>$1$2</b>");

  // 3. Heal suffix severed: الع<b>لاقة</b>
  healed = healed.replace(/([\u0600-\u06FF]+)<b>([\u0600-\u06FF]+)<\/b>/g, "<b>$1$2</b>");

  // 4. Remove lingering tatweel
  healed = healed.replace(/[\u0640]/g, "");

  // 5. Unbold functional particles / short stop words so attention focuses on content words
  healed = healed.replace(/<b>([\u0600-\u06FF]+)<\/b>/g, (m, word) => {
    const trimmed = word.trim();
    if (trimmed.length <= 2 || ARABIC_BIONIC_STOPS.has(trimmed)) {
      return trimmed;
    }
    return m;
  });

  return healed;
}

function populateGeneratedOutputs(data) {
  // 1. Simulation Lab View
  $("empty-lab").style.display = "none";
  $("active-lab").style.display = "block";
  const labTitle = (data.verified_lab && data.verified_lab.title)
    || (data.simulation_spec && data.simulation_spec.title)
    || $("input-topic").value.trim()
    || (data.lesson_input && data.lesson_input.topic)
    || data.topic
    || "STEM Lab";
  $("lab-topic-title").textContent = labTitle;

  const frame = $("lab-frame");
  const htmlContent = (data.verified_lab && data.verified_lab.html_content) || data.lab_html || data.simulation_html || "<html><body><h3>Lab generated</h3></body></html>";
  frame.srcdoc = htmlContent;

  // 2. Sensory Suite View
  $("empty-sensory").style.display = "none";
  $("active-sensory").style.display = "block";

  const acc = data.accessibility || data.sensory_suite || {};
  const adhdContainer = $("adhd-steps");
  adhdContainer.innerHTML = "";
  const steps = acc.adhd_steps || [
    { title: "Step 1: Observe Setup", description: "Familiarize yourself with the initial state." },
    { title: "Step 2: Change Variable", description: "Adjust one parameter at a time." },
    { title: "Step 3: Analyze Reaction", description: "Record the mathematical output." }
  ];

  steps.forEach((st, idx) => {
    const card = document.createElement("div");
    card.className = "adhd-step-card";
    let title = `Step ${idx + 1}`;
    let desc = "";
    if (typeof st === "string") {
      const parts = st.split(":");
      if (parts.length > 1) {
        title = parts[0].trim();
        desc = parts.slice(1).join(":").trim();
      } else {
        desc = st.trim();
      }
    } else if (typeof st === "object" && st !== null) {
      title = st.title || st.step_title || `Step ${idx + 1}`;
      desc = st.description || st.step_description || "";
    }
    card.innerHTML = `
      <div class="adhd-step-num">${idx + 1}</div>
      <div class="adhd-step-title">${title}</div>
      <div class="adhd-step-desc">${desc}</div>
    `;
    adhdContainer.appendChild(card);
  });

  const bionicBox = $("bionic-content");
  const bionicHtml = acc.bionic_reading_html || $("input-text").value;
  bionicBox.innerHTML = sanitizeArabicBionic(bionicHtml);

  const kitchenBox = $("kitchen-content");
  let kitchenDesc = "";
  if (acc.home_experiment) {
    const exp = acc.home_experiment;
    kitchenDesc = `<div style="font-size:14.5px; font-weight:800; color:var(--slate-900); margin-bottom:8px;">${exp.title || 'Home Kitchen Experiment'}</div>`;
    if (exp.materials && exp.materials.length) {
      kitchenDesc += `<div style="font-size:13px; color:var(--text-secondary); margin-bottom:10px;"><strong>Materials:</strong> ${exp.materials.join(', ')}</div>`;
    }
    const expSteps = exp.steps || exp.instructions || [];
    if (expSteps && expSteps.length) {
      kitchenDesc += `<ol style="padding-inline-start:20px; font-size:13.5px; line-height:1.7; color:var(--slate-800);">${expSteps.map(i => `<li>${i}</li>`).join('')}</ol>`;
    }
    if (exp.safety_note) {
      kitchenDesc += `<div style="font-size:12.5px; color:#b91c1c; margin-top:10px; font-weight:600;">⚠️ ${exp.safety_note}</div>`;
    }
  } else {
    kitchenDesc = `<p style="font-size:14px; line-height:1.6; color:var(--slate-800);">${acc.kitchen_lab || (currentLang === "en" ? "Use everyday items to replicate this physical relationship." : "استخدم أدوات منزلية بسيطة لتطبيق هذه العلاقة الفيزيائية.")}</p>`;
  }
  kitchenBox.innerHTML = kitchenDesc;

  // 3. Mastery View
  $("empty-mastery").style.display = "none";
  $("active-mastery").style.display = "block";

  // Populate Voice Companion with dual-engine support
  populateVoiceCompanion(data);

  const ch = data.challenge || data.socratic_challenge || {};
  const question = ch.challenge_question || ch.question || (currentLang === "en" ? "What happens when you adjust the parameters in this experiment?" : "ماذا تلاحظ عند تغيير المعاملات في هذا المعمل؟");
  const hint = ch.challenge_hint || ch.hint || (currentLang === "en" ? "Review the formula relationship in the simulation." : "تذكر العلاقة الرياضية في قانون المعمل.");
  const answer = ch.challenge_answer || ch.expected_answer || ch.model_answer || ch.challenge_solution || (currentLang === "en" ? "The output scales in direct proportion according to the law." : "تتغير النتيجة بنسبة طردية مباشرة وفق القانون العلمي.");

  $("socratic-question").textContent = question;
  $("hint-content").textContent = hint;
  $("answer-content").textContent = answer;

  $("hint-panel").classList.remove("open");
  $("answer-panel").classList.remove("open");
  $("btn-txt-hint").textContent = I18N[currentLang].btnHintReveal;
  $("btn-txt-answer").textContent = I18N[currentLang].btnAnswerReveal;

  // 4. Impact View Metrics
  const impact = data.impact || data.metrics || {};
  if (impact.baseline_grade_level && impact.simplified_grade_level) {
    const diff = (impact.baseline_grade_level - impact.simplified_grade_level).toFixed(1);
    $("stat-val-grade").textContent = `-${diff}`;
  }
  if (impact.lab_size_kb) {
    $("stat-val-size").textContent = `${impact.lab_size_kb.toFixed(1)} KB`;
  }
}

function resetLabFrame() {
  if (lastServerData) {
    const frame = $("lab-frame");
    frame.srcdoc = (lastServerData.verified_lab && lastServerData.verified_lab.html_content) || lastServerData.lab_html || lastServerData.simulation_html || "";
  }
}

function saveActiveLabToVault() {
  if (!lastServerData) {
    alert(currentLang === "en" ? "Please generate a lab first!" : "يرجى توليد معمل أولاً!");
    return;
  }

  const topic = $("input-topic").value.trim() || "STEM Lab";
  const subject = $("input-subject").value.trim() || "Science";
  const grade = $("input-grade").value.trim() || "8";
  const htmlContent = (lastServerData.verified_lab && lastServerData.verified_lab.html_content) || lastServerData.lab_html || lastServerData.simulation_html || "";

  // Extract authentic educational explanation
  const rawDescEn = (lastServerData.deconstructed && lastServerData.deconstructed.simplified_explanation)
    || (lastServerData.deconstructed && lastServerData.deconstructed.core_concept)
    || (lastServerData.lesson_input && lastServerData.lesson_input.raw_text)
    || `Interactive STEM simulation exploring ${topic}.`;
  const cleanDescEn = rawDescEn.length > 160 ? rawDescEn.slice(0, 157).trim() + "..." : rawDescEn;
  const cleanDescAr = (lastServerData.lesson_input && lastServerData.lesson_input.language === "ar")
    ? cleanDescEn
    : (lastServerData.deconstructed && lastServerData.deconstructed.simplified_explanation)
      || `محاكاة تفاعلية تعليمية لاستكشاف ${topic}.`;

  const labItem = {
    id: "saved_" + Date.now(),
    isCore: false,
    subjectEn: subject,
    subjectAr: subject,
    gradeEn: `Grade ${grade}`,
    gradeAr: `الصف ${grade}`,
    titleEn: topic,
    titleAr: topic,
    descEn: cleanDescEn,
    descAr: cleanDescAr,
    engine: "SYNTHESIZED ENGINE (SANDBOXED)",
    formula: lastServerData.formula || (lastServerData.simulation_spec && lastServerData.simulation_spec.formula_expression) || "Active Synthesis",
    html: htmlContent,
    deconstructed: lastServerData.deconstructed || null,
    simulation_spec: lastServerData.simulation_spec || null,
    accessibility: lastServerData.sensory_suite || lastServerData.accessibility || {},
    challenge: lastServerData.socratic_challenge || lastServerData.challenge || {},
    mastery: lastServerData.mastery || lastServerData.mastery_voice || {},
    audio: lastServerData.audio || lastServerData.mastery_voice || {},
    impact: lastServerData.impact || lastServerData.impact_ledger || {},
    savedAt: Date.now()
  };

  saveToVaultStorage(labItem);

  const toast = $("save-toast");
  if (toast) {
    toast.style.display = "inline-block";
    setTimeout(() => {
      toast.style.display = "none";
    }, 2800);
  }
}

function downloadLab() {
  const isAr = (currentLang === "ar");
  const data = (typeof getLastServerData === "function" ? getLastServerData() : lastServerData) || (typeof activeRuntimeLab !== "undefined" ? activeRuntimeLab : null) || CORE_LABS[0];
  const fullHtml = typeof buildStandaloneScenarioPackage === "function"
    ? buildStandaloneScenarioPackage(data, isAr)
    : (data.getHtml ? data.getHtml(isAr) : (data.html || ""));

  let title = (data.topic || (data.lesson_input && data.lesson_input.topic) || (data.simulation_spec && data.simulation_spec.title) || data.titleEn || (data.verified_lab && data.verified_lab.title) || "LuminaLab-Scenario").replace(/\s+/g, "_");

  const blob = new Blob([fullHtml], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${title}_Complete_Offline.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast(isAr ? "تم تنزيل السيناريو كاملاً بكل الأقسام بنجاح" : "Complete Multi-Tab Scenario downloaded successfully!");
}

// Socratic Reveal Toggles
function toggleHint() {
  const panel = $("hint-panel");
  const isOpen = panel.classList.toggle("open");
  $("btn-txt-hint").textContent = isOpen ? I18N[currentLang].btnHintHide : I18N[currentLang].btnHintReveal;
}

function toggleAnswer() {
  const panel = $("answer-panel");
  const isOpen = panel.classList.toggle("open");
  $("btn-txt-answer").textContent = isOpen ? I18N[currentLang].btnAnswerHide : I18N[currentLang].btnAnswerReveal;
}

function evaluateHypothesis() {
  const input = $("input-student-answer").value.trim();
  const feedback = $("hypothesis-feedback");

  if (!input) {
    feedback.style.display = "block";
    feedback.style.background = "#FEF2F2";
    feedback.style.color = "#991B1B";
    feedback.textContent = currentLang === "en" ? "Please enter your hypothesis before submitting." : "يرجى كتابة فرضيتك قبل الإرسال.";
    return;
  }

  feedback.style.display = "block";
  feedback.style.background = "#F0FDF4";
  feedback.style.color = "#166534";
  feedback.textContent = currentLang === "en"
    ? "✓ Hypothesis recorded. Compare your reasoning with the Pedagogical Hint and Model Explanation below."
    : "✓ تم تسجيل فرضيتك بنجاح. قارن تحليلك الآن مع التلميح التوجيهي والتفسير النموذجي أدناه.";
}

async function fetchLedgerStats() {
  try {
    const res = await fetch("/api/stats");
    if (res.ok) {
      const stats = await res.json();
      if ($("val-cumul-sessions")) $("val-cumul-sessions").textContent = stats.total_sessions || "0";
      if ($("val-cumul-reduction")) $("val-cumul-reduction").textContent = `${(stats.avg_grade_reduction || 0).toFixed(1)} Grades`;
      if ($("val-cumul-offline")) $("val-cumul-offline").textContent = stats.total_offline_ready_labs ? `${stats.total_offline_ready_labs} Labs` : "100%";
      if (stats.avg_cognitive_load_reduction_pct && $("stat-val-cog")) {
        $("stat-val-cog").textContent = `-${stats.avg_cognitive_load_reduction_pct.toFixed(0)}%`;
      }
      if (stats.avg_lab_size_kb && $("stat-val-size")) {
        $("stat-val-size").textContent = `${stats.avg_lab_size_kb.toFixed(1)} KB`;
      }
    }
  } catch (e) {
    console.error("Failed to fetch stats", e);
  }
}

// ============================================================

window.populateGeneratedOutputs = populateGeneratedOutputs;
window.formatArabicBionicPlain = formatArabicBionicPlain;
window.sanitizeArabicBionic = sanitizeArabicBionic;
window.resetLabFrame = resetLabFrame;
window.downloadLab = downloadLab;
window.toggleHint = toggleHint;
window.toggleAnswer = toggleAnswer;
window.evaluateHypothesis = evaluateHypothesis;
