// ============================================================
// LuminaLab Swarm — Online Curriculum Studio Controller
// ============================================================

function initStudioWorkflow() {
  const form = $("curriculum-form");
  if (form) {
    form.addEventListener("submit", handleGenerate);
  }
}
window.initStudioWorkflow = initStudioWorkflow;
