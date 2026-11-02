// ============================================================
// LuminaLab Swarm — Main Application Bootstrap
// ============================================================
// INITIALIZATION
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  const inputTxt = $("input-text");
  if (inputTxt) {
    inputTxt.addEventListener("input", () => {
      const len = inputTxt.value.trim().length;
      const t = I18N[currentLang];
      $("txt-char-counter").textContent = len === 0 ? t.readyToSend : `${len} ${t.charUnit}`;
    });
  }

  // Set default English
  applyLang("en");

  // Show default view
  switchView("studio");

  // Render initial vault
  renderVaultGrid();

  // Initialize Voice Companion player and audio event listeners
  initVoiceAudioListeners();
  populateVoiceCompanion(null);

  // Check health and live cloud status
  fetch("/api/health")
    .then(r => r.json())
    .then(data => {
      if (data && data.mock_mode === false) {
        isMockMode = false;
        if ($("header-status-text")) {
          $("header-status-text").textContent = I18N[currentLang].statusCloud;
        }
      }
    })
    .catch(() => { });
});
