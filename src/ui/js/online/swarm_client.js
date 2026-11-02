// ============================================================
// LuminaLab Swarm — Online Pipeline Client & Telemetry
// ============================================================
// CLOUD PIPELINE EXECUTION (/api/generate)
// ============================================================
async function handleGenerate(e) {
  if (e) {
    if (typeof e.preventDefault === "function") e.preventDefault();
    if (typeof e.stopPropagation === "function") e.stopPropagation();
  }
  const t = I18N[currentLang];

  const subject = $("input-subject").value.trim() || "Physics";
  const grade = $("input-grade").value.trim() || "8";
  const topic = $("input-topic").value.trim() || "STEM Lab";
  const text = $("input-text").value.trim();

  if (!text || text.length < 5) {
    showToast(currentLang === "ar" ? "يرجى إدخال نص الدرس للشرح والمحاكاة" : "Please enter textbook lesson content", true);
    return;
  }

  const btnRun = $("btn-run");
  btnRun.disabled = true;

  const stepper = $("pipeline-stepper");
  const stepsContainer = $("pipeline-steps-container");
  const statusTitle = $("pipeline-status-title");

  stepper.style.display = "block";
  stepsContainer.innerHTML = "";
  if (statusTitle) {
    statusTitle.textContent = t.pipelineTitle || "Strands multi-agent pipeline executing...";
  }

  t.pipelineSteps.forEach((stepText, idx) => {
    const row = document.createElement("div");
    row.className = "step-row";
    row.id = `step-row-${idx}`;
    row.innerHTML = `
      <div class="step-indicator">${idx + 1}</div>
      <div class="step-desc-text">${stepText}</div>
    `;
    stepsContainer.appendChild(row);
  });

  const setStepState = (idx, state) => {
    const r = $(`step-row-${idx}`);
    if (!r) return;
    r.classList.remove("active", "completed", "error");
    if (state) r.classList.add(state);
  };

  // Launch network request concurrently
  const requestPromise = fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      subject: subject,
      topic: topic,
      student_grade: parseInt(grade, 10) || 8,
      raw_text: text,
      language: currentLang || "en"
    })
  });

  try {
    // Progressive fluid feedback:
    // Step 0: Agent 1A
    setStepState(0, "active");
    await new Promise(r => setTimeout(r, 260));
    setStepState(0, "completed");

    // Step 1: Agent 1B
    setStepState(1, "active");
    await new Promise(r => setTimeout(r, 260));
    setStepState(1, "completed");

    // Step 2: Agent 2A (Synthesis)
    setStepState(2, "active");

    // Await server response
    const response = await requestPromise;

    if (!response.ok) {
      let errMsg = `HTTP ${response.status}`;
      let errDetails = null;
      try {
        const errJson = await response.json();
        errDetails = errJson;
        if (currentLang === "ar" && errJson.message_ar) {
          errMsg = errJson.title_ar ? `${errJson.title_ar} — ${errJson.message_ar}` : errJson.message_ar;
          if (errJson.hint_ar) errMsg += ` [💡 ${errJson.hint_ar}]`;
        } else if (errJson.message) {
          errMsg = errJson.title ? `${errJson.title} — ${errJson.message}` : errJson.message;
          if (errJson.hint) errMsg += ` [💡 ${errJson.hint}]`;
        } else if (errJson.error) {
          errMsg = errJson.error;
        } else if (errJson.detail) {
          errMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch (_) { }
      const customErr = new Error(errMsg);
      customErr.details = errDetails;
      throw customErr;
    }

    const data = await response.json();
    lastServerData = data;

    // Complete Step 2
    setStepState(2, "completed");

    // Rapidly complete steps 3, 4, 5
    for (let i = 3; i < t.pipelineSteps.length; i++) {
      setStepState(i, "active");
      await new Promise(r => setTimeout(r, 140));
      setStepState(i, "completed");
    }

    if (statusTitle) {
      statusTitle.textContent = currentLang === "ar" ? "اكتمل توليد المحاكاة بنجاح!" : "Swarm synthesis completed successfully!";
    }

    // Populate all views with generated outputs
    populateGeneratedOutputs(data);

    // Automatically transition to Simulation Lab view so user sees result!
    setTimeout(() => {
      switchView("lab");
    }, 220);

  } catch (err) {
    console.error("Generation error:", err);
    if (statusTitle) {
      statusTitle.textContent = (currentLang === "ar" ? "تعذر التوليد: " : "Generation failed: ") + err.message;
    }
    const activeRow = stepsContainer.querySelector(".step-row.active");
    if (activeRow) {
      activeRow.classList.remove("active");
      activeRow.classList.add("error");
    }
    showToast((currentLang === "ar" ? "حدث خطأ: " : "Error: ") + err.message, true);
  } finally {
    btnRun.disabled = false;
  }
}

const ARABIC_BIONIC_STOPS = new Set([
  "في", "من", "إلى", "على", "عن", "مع", "بين", "حيث", "هو", "هي", "هما", "هم", "هن",
  "هذا", "هذه", "ذلك", "تلك", "هؤلاء", "أولئك", "الذي", "التي", "الذين", "اللاتي", "اللواتي",
  "أن", "إن", "ما", "لا", "لم", "لن", "ليس", "غير", "سوى", "إلا",
  "عند", "قبل", "بعد", "ثم", "أو", "أم", "بل", "إذا", "لو", "كل", "كلما",
  "وذلك", "كذلك", "بما", "كما", "وقد", "فقد", "حتى", "كي", "لكن", "لأن"
]);


window.handleGenerate = handleGenerate;
