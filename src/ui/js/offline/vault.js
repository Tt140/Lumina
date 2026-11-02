// ============================================================
// LuminaLab Swarm — Offline Vault Storage & Scenario Persistence
// ============================================================
// LOCAL STORAGE VAULT MANAGEMENT
// ============================================================
const STORAGE_KEY = "lumina_offline_vault";

function getStoredVault() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    let list = JSON.parse(raw);
    if (!Array.isArray(list)) return [];

    let modified = false;
    list = list.map(item => {
      if (!item || typeof item !== "object") return item;

      // 1. Heal truncated title
      if (item.titleEn && item.titleEn.includes("Equilibriu") && !item.titleEn.includes("Equilibrium")) {
        item.titleEn = item.titleEn.replace("Equilibriu", "Equilibrium");
        if (item.titleAr && item.titleAr.includes("Equilibriu")) item.titleAr = item.titleEn;
        modified = true;
      }

      // 2. Heal robotic description
      if (item.descEn && (item.descEn.includes("Saved from Live Cloud Studio") || item.descEn.includes("تم الحفظ من استوديو السحابة"))) {
        const title = item.titleEn || "";
        if (title.toLowerCase().includes("buffer") || title.toLowerCase().includes("henderson")) {
          item.descEn = "A buffer solution resists drastic changes in pH upon the addition of small amounts of acid or base, governed by the Henderson-Hasselbalch equation.";
          item.descAr = "يقاوم المحلول المنظم التغيرات المفاجئة في الرقم الهيدروجيني عند إضافة كميات من الحمض أو القاعدة وفق معادلة هندرسون-هاسلبالخ.";
        } else if (title.toLowerCase().includes("hooke") || title.toLowerCase().includes("spring")) {
          item.descEn = "Explore restoring force, spring constant, and mechanical displacement according to Hooke's Law.";
          item.descAr = "استكشف قوة الإرجاع وثابت المرونة والاستطالة في النوابض والزنبرك وفق قانون هوك.";
        } else if (title.toLowerCase().includes("lever") || title.toLowerCase().includes("seesaw")) {
          item.descEn = "Investigate mechanical advantage, torque equilibrium, and rotational balance across lever arms.";
          item.descAr = "اختبر الفائدة الميكانيكية، واتزان العزوم، ونقطة الارتكاز وقوانين الروافع.";
        } else if (title.toLowerCase().includes("acid") || title.toLowerCase().includes("base")) {
          item.descEn = "Interactive pH scale measuring hydrogen and hydroxide ion concentrations across acidic and basic solutions.";
          item.descAr = "محاكاة تفاعلية لمقياس الرقم الهيدروجيني وتراكيز أيونات الهيدروجين في المحاليل الحمضية والقاعدية.";
        } else {
          item.descEn = `Interactive STEM simulation investigating fundamental principles of ${title}.`;
          item.descAr = `محاكاة تعليمية تفاعلية لاستكشاف وتطبيق مبادئ ${item.titleAr || title}.`;
        }
        modified = true;
      }

      // 3. Heal pH domain bounds in legacy simulation HTML and contracts
      const isCellOrBiology = (item.html && item.html.includes('archetype = "cell"')) ||
                              (item.formula && item.formula.includes("V_cell")) ||
                              (item.descEn && /osmosis|membrane|cell volume/i.test(item.descEn));

      const isPhRelated = !isCellOrBiology && (
                          (item.titleEn && /\bph scale\b|\bph lab\b|henderson/i.test(item.titleEn)) ||
                          (item.formula && (item.formula.startsWith("pH =") || item.formula.includes("pKa + log10"))) ||
                          (item.html && (item.html.includes("pH =") || item.html.includes("pKa + log10")))
                        );

      if (isPhRelated) {
        // Heal HTML progress bar bounds if mistakenly set to 100
        if (item.html && typeof item.html === "string") {
          if (item.html.includes("boundMax = 100.0;") || item.html.includes("boundMax = 100;")) {
            item.html = item.html
              .replace(/let boundMin = [0-9.]+;/g, "let boundMin = 0.0;")
              .replace(/var boundMin = [0-9.]+;/g, "var boundMin = 0.0;")
              .replace(/const boundMin = [0-9.]+;/g, "const boundMin = 0.0;")
              .replace(/let boundMax = 100(\.0)?;/g, "let boundMax = 14.0;")
              .replace(/var boundMax = 100(\.0)?;/g, "var boundMax = 14.0;")
              .replace(/const boundMax = 100(\.0)?;/g, "const boundMax = 14.0;")
              .replace(/const isLogScale = true;/g, "const isLogScale = false;");
            modified = true;
          }
        }

        // Heal simulation_spec bounds if present
        if (item.simulation_spec) {
          if (item.simulation_spec.result_max === 100.0 && item.simulation_spec.result_min === 0.0) {
            item.simulation_spec.result_min = 0.0;
            item.simulation_spec.result_max = 14.0;
            item.simulation_spec.result_symbol = "pH";
            item.simulation_spec.is_logarithmic_output = false;
            modified = true;
          }
        }
      }

      // 4. Heal mechanical lever specs if present
      const isLeverRelated = (item.titleEn && /\blever\b|seesaw|balance|torque/i.test(item.titleEn));
      if (isLeverRelated && item.simulation_spec) {
        if (item.simulation_spec.result_symbol !== "Balance") {
          item.simulation_spec.result_symbol = "Balance";
          item.simulation_spec.result_min = 0.0;
          item.simulation_spec.result_max = 100.0;
          item.simulation_spec.is_logarithmic_output = false;
          modified = true;
        }
      }
      return item;
    });

    if (modified) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    }

    return list;
  } catch (e) {
    console.error("Failed to read vault from localStorage", e);
    return [];
  }
}

function saveToVaultStorage(labItem) {
  try {
    const list = getStoredVault();
    list.unshift(labItem);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    updateVaultBadges();
    return true;
  } catch (e) {
    console.error("Failed to save to vault", e);
    return false;
  }
}

function deleteFromVaultStorage(id) {
  try {
    let list = getStoredVault();
    list = list.filter(item => item.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    updateVaultBadges();
    renderVaultGrid();
  } catch (e) {
    console.error("Failed to delete from vault", e);
  }
}

function updateVaultBadges() {
  const saved = getStoredVault();
  const total = CORE_LABS.length + saved.length;
  if ($("vault-count-badge")) $("vault-count-badge").textContent = total;
  if ($("count-all")) $("count-all").textContent = total;
  if ($("count-saved")) $("count-saved").textContent = saved.length;
}

// ============================================================

// OFFLINE VAULT LIBRARY RENDERING
// ============================================================
var currentVaultFilter = "all";
window.currentVaultFilter = currentVaultFilter;

function filterVault(filterType) {
  currentVaultFilter = filterType;
  $("filter-all").classList.toggle("active", filterType === "all");
  $("filter-core").classList.toggle("active", filterType === "core");
  $("filter-saved").classList.toggle("active", filterType === "saved");
  renderVaultGrid();
}

function renderVaultGrid() {
  const grid = $("vault-grid");
  if (!grid) return;
  grid.innerHTML = "";

  const savedList = getStoredVault();
  let labsToDisplay = [];

  if (currentVaultFilter === "all") {
    labsToDisplay = [...CORE_LABS, ...savedList];
  } else if (currentVaultFilter === "core") {
    labsToDisplay = [...CORE_LABS];
  } else if (currentVaultFilter === "saved") {
    labsToDisplay = [...savedList];
  }

  updateVaultBadges();

  if (labsToDisplay.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align:center; padding:40px; color:var(--text-muted); background:var(--surface-subtle); border-radius:16px;">
        <p style="font-weight:700; font-size:15px;">${currentLang === "en" ? "No saved labs in this category." : "لا توجد معامل محفوظة في هذا التصنيف."}</p>
        <p style="font-size:13px; margin-top:6px;">${currentLang === "en" ? "Generate a simulation in Curriculum Studio and click 'Save to Offline Vault'." : "قم بتوليد محاكاة من استوديو المناهج واضغط 'حفظ في الخزنة الأوفلاين'."}</p>
      </div>
    `;
    return;
  }

  labsToDisplay.forEach(lab => {
    const isAr = currentLang === "ar";
    const title = isAr ? (lab.titleAr || lab.titleEn) : lab.titleEn;
    const subject = isAr ? (lab.subjectAr || lab.subjectEn) : lab.subjectEn;
    const grade = isAr ? (lab.gradeAr || lab.gradeEn) : lab.gradeEn;
    const desc = isAr ? (lab.descAr || lab.descEn) : lab.descEn;
    const isCore = lab.isCore;

    const card = document.createElement("div");
    card.className = "vault-card";
    card.innerHTML = `
      <div class="vault-card-header">
        <div class="vault-icon-circle">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            ${isCore ? '<polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline>' : '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>'}
          </svg>
        </div>
        <div class="vault-header-actions">
          <span class="vault-badge-tag ${isCore ? 'tag-core' : 'tag-saved'}">
            ${isCore ? I18N[currentLang].vaultTagCore : I18N[currentLang].vaultTagSaved}
          </span>
          ${!isCore ? `
            <button type="button" class="vault-delete-btn" onclick="deleteFromVaultStorage('${lab.id}')" title="${isAr ? 'حذف من الخزنة' : 'Delete from Vault'}" aria-label="Delete">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
            </button>
          ` : ''}
        </div>
      </div>

      <div class="vault-title">${title}</div>
      <div class="vault-desc">${desc}</div>

      <div class="vault-meta-footer">
        <div class="vault-meta-text">${subject} • ${grade}</div>
        <button type="button" class="btn-pill btn-pill-primary btn-pill-sm vault-launch-btn" onclick="launchVaultLab('${lab.id}')">
          ${I18N[currentLang].btnLaunchVault}
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function downloadVaultScenario(labId) {
  let lab = CORE_LABS.find(l => l.id === labId);
  if (!lab) {
    const saved = getStoredVault();
    lab = saved.find(l => l.id === labId);
  }
  if (!lab) return;

  const isAr = (currentLang === "ar");
  const fullHtml = typeof buildStandaloneScenarioPackage === "function" 
    ? buildStandaloneScenarioPackage(lab, isAr)
    : (lab.getHtml ? lab.getHtml(isAr) : (lab.html || ""));
  const title = (lab.titleEn || lab.titleAr || (lab.lesson_input && lab.lesson_input.topic) || (lab.simulation_spec && lab.simulation_spec.title) || lab.topic || "Offline-Scenario").replace(/\s+/g, "_");

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

// ============================================================

window.STORAGE_KEY = STORAGE_KEY;
window.getStoredVault = getStoredVault;
window.saveToVaultStorage = saveToVaultStorage;
window.deleteFromVaultStorage = deleteFromVaultStorage;
window.updateVaultBadges = updateVaultBadges;
window.filterVault = filterVault;
window.renderVaultGrid = renderVaultGrid;
if (typeof saveActiveLabToVault !== "undefined") window.saveActiveLabToVault = saveActiveLabToVault;
window.downloadVaultScenario = downloadVaultScenario;
