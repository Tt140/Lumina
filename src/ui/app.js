// DUAL-ENGINE STUDIO VOICE COMPANION & AUDIO CONTROLLER
// ============================================================
let activeAudioEngine = "polly"; // 'polly' (AWS S3) or 'native' (Web Speech API)
let currentVoiceSpeed = 1.0;
let currentVoiceScript = "";
let currentAudioUrl = "";
let isPlayingVoice = false;
let nativeSpeechTimer = null;
let nativeSpeechDurationEst = 0;

function populateVoiceCompanion(data) {
  const acc = (data && (data.accessibility || data.sensory_suite)) || {};

  // Extract voice script
  let script = "";
  if (acc.voice_script) {
    if (typeof acc.voice_script === "string") {
      script = acc.voice_script;
    } else if (typeof acc.voice_script === "object") {
      script = currentLang === "ar" ? (acc.voice_script.ar || acc.voice_script.en) : (acc.voice_script.en || acc.voice_script.ar);
    }
  } else if (data && data.voice_script) {
    script = data.voice_script;
  }

  if (!script || !script.trim()) {
    const topic = $("input-topic") ? $("input-topic").value.trim() : "";
    const gradeVal = parseInt($("input-grade") ? $("input-grade").value : "8", 10) || 8;
    if (gradeVal >= 10) {
      if (currentLang === "ar") {
        script = `مرحباً بك في تجربة ${topic || 'العلوم التفاعلية'}. استكشف المبادئ العلمية الأساسية، ولاحظ كيف تتغير النتائج مباشرة مع تحريك عناصر التحكم في المحاكاة.`;
      } else {
        script = `Welcome to your ${topic || 'STEM'} interactive simulation. Explore the core scientific principles and observe how the output responds dynamically as you adjust the simulation parameters.`;
      }
    } else {
      if (currentLang === "ar") {
        script = `أهلاً بك في تجربة ${topic || 'العلوم الممتعة'}! جرب تحرك وتكتشف بنفسك وشوف النتيجة الممتعة بتظهر قدامك في ثواني وزي الفل!`;
      } else {
        script = `Welcome to your ${topic || 'STEM'} adventure! Explore the controls and watch the physical reactions happen right before your eyes!`;
      }
    }
  }
  currentVoiceScript = script.trim();

  const scriptEl = $("voice-script-text");
  if (scriptEl) scriptEl.textContent = currentVoiceScript;

  // Extract audio URL
  let audioUrl = "";
  if (data) {
    if (data.polly_audio_url) {
      audioUrl = data.polly_audio_url;
    } else if (acc.voice_audio && acc.voice_audio.audio_url) {
      audioUrl = acc.voice_audio.audio_url;
    } else if (acc.voice_audio_url) {
      audioUrl = acc.voice_audio_url;
    } else if (data.audio_url) {
      audioUrl = data.audio_url;
    }
  }

  currentAudioUrl = audioUrl ? audioUrl.trim() : "";
  const audioEl = $("voice-audio-element");
  const downloadBtn = $("btn-download-audio");

  if (currentAudioUrl) {
    activeAudioEngine = "polly";
    if (audioEl) {
      audioEl.src = currentAudioUrl;
      if (typeof audioEl.load === "function") audioEl.load();
    }
    if (downloadBtn) {
      downloadBtn.style.display = "inline-flex";
      downloadBtn.href = currentAudioUrl;
    }
  } else {
    activeAudioEngine = "native";
    if (audioEl) {
      audioEl.removeAttribute("src");
    }
    if (downloadBtn) {
      downloadBtn.style.display = "none";
    }
  }

  updateVoiceBadge();
  resetVoicePlayerUI();
}

function populateVoiceFromLab(lab, isAr) {
  if (!lab) return;
  const acc = lab.accessibility || {};
  let script = "";
  if (acc.voice_script) {
    script = isAr ? (acc.voice_script.ar || acc.voice_script) : (acc.voice_script.en || acc.voice_script);
  }
  let audioUrl = "";
  if (acc.audio_url) {
    audioUrl = isAr ? (acc.audio_url.ar || acc.audio_url) : (acc.audio_url.en || acc.audio_url);
  } else if (lab.audio_url) {
    audioUrl = isAr ? (lab.audio_url.ar || lab.audio_url) : (lab.audio_url.en || lab.audio_url);
  } else if (lab.polly_audio_url) {
    audioUrl = lab.polly_audio_url;
  }
  populateVoiceCompanion({
    accessibility: {
      voice_script: script
    },
    polly_audio_url: audioUrl || ""
  });
}

function updateVoiceBadge() {
  const badgeEl = $("voice-engine-badge");
  const textEl = $("voice-engine-text");
  if (!badgeEl || !textEl) return;

  const t = I18N[currentLang] || I18N.en;
  if (activeAudioEngine === "polly") {
    badgeEl.className = "badge-status badge-success";
    textEl.textContent = t.voiceEnginePolly || "AWS Polly Neural 🎙️";
  } else {
    badgeEl.className = "badge-status badge-info";
    textEl.textContent = t.voiceEngineNative || "Offline Browser Voice 🔊";
  }
}

function resetVoicePlayerUI() {
  stopNativeVoice();
  const audioEl = $("voice-audio-element");
  if (audioEl) {
    if (typeof audioEl.pause === "function") audioEl.pause();
    audioEl.currentTime = 0;
  }
  isPlayingVoice = false;
  updateVoicePlayIcon(false);

  const slider = $("voice-progress-slider");
  if (slider) slider.value = 0;

  const curTime = $("voice-current-time");
  if (curTime) curTime.textContent = "0:00";

  const totTime = $("voice-total-duration");
  if (totTime) {
    if (activeAudioEngine === "native") {
      const words = currentVoiceScript.split(/\s+/).filter(Boolean).length;
      nativeSpeechDurationEst = Math.max(5, Math.round((words / 130) * 60 / currentVoiceSpeed));
      totTime.textContent = formatAudioTime(nativeSpeechDurationEst);
    } else {
      totTime.textContent = "0:00";
    }
  }
}

function initVoiceAudioListeners() {
  const audioEl = $("voice-audio-element");
  if (!audioEl) return;

  audioEl.addEventListener("loadedmetadata", () => {
    if (audioEl.duration && !isNaN(audioEl.duration)) {
      const totTime = $("voice-total-duration");
      if (totTime) totTime.textContent = formatAudioTime(audioEl.duration);
    }
  });

  audioEl.addEventListener("timeupdate", () => {
    if (activeAudioEngine !== "polly") return;
    const curTime = $("voice-current-time");
    if (curTime) curTime.textContent = formatAudioTime(audioEl.currentTime);

    const slider = $("voice-progress-slider");
    if (slider && audioEl.duration) {
      slider.value = (audioEl.currentTime / audioEl.duration) * 100;
    }
  });

  audioEl.addEventListener("play", () => {
    isPlayingVoice = true;
    updateVoicePlayIcon(true);
  });

  audioEl.addEventListener("pause", () => {
    isPlayingVoice = false;
    updateVoicePlayIcon(false);
  });

  audioEl.addEventListener("ended", () => {
    isPlayingVoice = false;
    updateVoicePlayIcon(false);
    const slider = $("voice-progress-slider");
    if (slider) slider.value = 0;
    const curTime = $("voice-current-time");
    if (curTime) curTime.textContent = "0:00";
  });

  // Hackathon Resilience: If remote Polly stream fails to load, gracefully fall back to Native Web Speech API!
  audioEl.addEventListener("error", () => {
    console.warn("Polly audio playback encountered network/source error. Switching to Native Web Speech API fallback.");
    activeAudioEngine = "native";
    updateVoiceBadge();
    const downloadBtn = $("btn-download-audio");
    if (downloadBtn) downloadBtn.style.display = "none";
    if (isPlayingVoice) {
      speakNativeVoice();
    }
  });
}

function toggleVoicePlayback() {
  const audioEl = $("voice-audio-element");

  if (isPlayingVoice) {
    if (activeAudioEngine === "polly" && audioEl) {
      audioEl.pause();
    } else {
      stopNativeVoice();
    }
  } else {
    if (activeAudioEngine === "polly" && audioEl && audioEl.src) {
      audioEl.playbackRate = currentVoiceSpeed;
      audioEl.play().catch(err => {
        console.warn("HTML5 audio play failed, requesting on-demand neural Polly TTS:", err);
        fetchAndPlayPollyTTS();
      });
    } else {
      fetchAndPlayPollyTTS();
    }
  }
}

async function fetchAndPlayPollyTTS() {
  const isAr = currentLang === "ar" || /[\u0600-\u06FF]/.test(currentVoiceScript);
  const audioEl = $("voice-audio-element");

  if (currentVoiceScript && currentVoiceScript.trim()) {
    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: currentVoiceScript.trim(),
          language: isAr ? "ar" : "en"
        })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.audio_url && audioEl) {
          currentAudioUrl = data.audio_url;
          activeAudioEngine = "polly";
          audioEl.src = currentAudioUrl;
          audioEl.playbackRate = currentVoiceSpeed;
          updateVoiceBadge();
          await audioEl.play();
          return;
        }
      }
    } catch (err) {
      console.warn("On-demand Polly TTS error, falling back to female native speech:", err);
    }
  }

  speakNativeVoice();
}

function updateVoicePlayIcon(playing) {
  const iconPlay = $("icon-voice-play");
  const iconPause = $("icon-voice-pause");
  if (iconPlay) iconPlay.style.display = playing ? "none" : "block";
  if (iconPause) iconPause.style.display = playing ? "block" : "none";
}

function restartVoicePlayback() {
  const audioEl = $("voice-audio-element");
  if (activeAudioEngine === "polly" && audioEl && audioEl.src) {
    audioEl.currentTime = 0;
    audioEl.playbackRate = currentVoiceSpeed;
    audioEl.play().catch(() => { });
  } else {
    stopNativeVoice();
    speakNativeVoice();
  }
}

function seekVoicePlayback(val) {
  const percent = parseFloat(val);
  const audioEl = $("voice-audio-element");
  if (activeAudioEngine === "polly" && audioEl && audioEl.duration) {
    audioEl.currentTime = (percent / 100) * audioEl.duration;
  } else if (activeAudioEngine === "native") {
    stopNativeVoice();
    speakNativeVoice();
  }
}

function setVoiceSpeed(speed) {
  currentVoiceSpeed = parseFloat(speed) || 1.0;
  const audioEl = $("voice-audio-element");
  if (audioEl) {
    audioEl.playbackRate = currentVoiceSpeed;
  }

  // Update speed pill styles
  document.querySelectorAll(".speed-pill").forEach(pill => {
    const s = parseFloat(pill.getAttribute("data-speed"));
    if (Math.abs(s - currentVoiceSpeed) < 0.05) {
      pill.classList.add("active");
    } else {
      pill.classList.remove("active");
    }
  });

  // Re-estimate duration for native mode
  if (activeAudioEngine === "native") {
    const words = currentVoiceScript.split(/\s+/).filter(Boolean).length;
    nativeSpeechDurationEst = Math.max(5, Math.round((words / 130) * 60 / currentVoiceSpeed));
    const totTime = $("voice-total-duration");
    if (totTime) totTime.textContent = formatAudioTime(nativeSpeechDurationEst);
  }

  // If speaking natively, restart with new speed rate
  if (isPlayingVoice && activeAudioEngine === "native") {
    stopNativeVoice();
    speakNativeVoice();
  }
}

function toggleVoiceTranscript() {
  const body = $("voice-transcript-body");
  const icon = $("transcript-toggle-icon");
  if (!body) return;
  const isOpen = body.classList.contains("open");
  if (isOpen) {
    body.classList.remove("open");
    if (icon) icon.style.transform = "rotate(0deg)";
  } else {
    body.classList.add("open");
    if (icon) icon.style.transform = "rotate(180deg)";
  }
}

function speakNativeVoice() {
  if (!('speechSynthesis' in window)) {
    showToast(currentLang === "ar" ? "المتصفح لا يدعم تحويل النص إلى صوت." : "Speech synthesis is not supported in this browser.", true);
    return;
  }

  window.speechSynthesis.cancel();
  if (!currentVoiceScript) return;

  const utterance = new SpeechSynthesisUtterance(currentVoiceScript);
  window.activeVoiceUtterance = utterance; // Prevent Chrome GC cutoff bug
  const isAr = currentLang === "ar" || /[\u0600-\u06FF]/.test(currentVoiceScript);
  utterance.lang = isAr ? "ar-EG" : "en-US";
  utterance.rate = currentVoiceSpeed;

  const voices = window.speechSynthesis.getVoices();
  if (voices && voices.length) {
    const maleNames = ["maged", "tariq", "tarik", "david", "guy", "mark", "george", "richard", "naayf", "male", "youssef", "omar", "stefan", "fred", "daniel"];
    const isMale = (name) => {
      const lower = (name || "").toLowerCase();
      return maleNames.some(m => lower.includes(m)) && !lower.includes("female");
    };

    if (isAr) {
      const femaleAr = voices.filter(v => v.lang.toLowerCase().startsWith("ar") && !isMale(v.name));
      const matched = femaleAr.find(v => v.lang.includes("EG") || v.name.includes("Salma") || v.name.includes("Laila") || v.name.includes("Mariam") || v.name.includes("Hala") || v.name.includes("Zeina")) ||
        femaleAr.find(v => v.name.toLowerCase().includes("female")) ||
        femaleAr[0];
      if (matched) utterance.voice = matched;
    } else {
      const femaleEn = voices.filter(v => v.lang.toLowerCase().startsWith("en") && !isMale(v.name));
      const matched = femaleEn.find(v => v.name.includes("Jenny") || v.name.includes("Joanna") || v.name.includes("Zira") || v.name.includes("Samantha") || v.name.includes("Victoria") || v.name.includes("Aria")) ||
        femaleEn.find(v => v.name.toLowerCase().includes("female")) ||
        femaleEn[0];
      if (matched) utterance.voice = matched;
    }
  }

  const words = currentVoiceScript.split(/\s+/).filter(Boolean).length;
  nativeSpeechDurationEst = Math.max(5, Math.round((words / 130) * 60 / currentVoiceSpeed));
  const totTime = $("voice-total-duration");
  if (totTime) totTime.textContent = formatAudioTime(nativeSpeechDurationEst);

  const startTime = Date.now();

  utterance.onstart = () => {
    isPlayingVoice = true;
    updateVoicePlayIcon(true);

    clearInterval(nativeSpeechTimer);
    nativeSpeechTimer = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000;
      const curTime = $("voice-current-time");
      if (curTime) curTime.textContent = formatAudioTime(Math.min(elapsed, nativeSpeechDurationEst));

      const slider = $("voice-progress-slider");
      if (slider) {
        slider.value = Math.min(100, (elapsed / nativeSpeechDurationEst) * 100);
      }
    }, 200);
  };

  utterance.onend = () => {
    window.activeVoiceUtterance = null;
    stopNativeVoice();
  };

  utterance.onerror = (e) => {
    console.error("SpeechSynthesis error:", e);
    window.activeVoiceUtterance = null;
    stopNativeVoice();
  };

  window.speechSynthesis.speak(utterance);
}

function stopNativeVoice() {
  isPlayingVoice = false;
  updateVoicePlayIcon(false);
  clearInterval(nativeSpeechTimer);
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
}

function formatAudioTime(seconds) {
  if (isNaN(seconds) || seconds < 0) return "0:00";
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}

// Explicit window bindings for inline HTML handlers & global invocation
window.toggleVoicePlayback = toggleVoicePlayback;
window.restartVoicePlayback = restartVoicePlayback;
window.seekVoicePlayback = seekVoicePlayback;
window.setVoiceSpeed = setVoiceSpeed;
window.toggleVoiceTranscript = toggleVoiceTranscript;
window.populateVoiceCompanion = populateVoiceCompanion;
window.populateVoiceFromLab = populateVoiceFromLab;
window.updateVoiceBadge = updateVoiceBadge;
window.resetVoicePlayerUI = resetVoicePlayerUI;
window.getActiveAudioEngine = () => activeAudioEngine;
window.getIsPlayingVoice = () => isPlayingVoice;
window.getCurrentVoiceSpeed = () => currentVoiceSpeed;
window.getCurrentVoiceScript = () => currentVoiceScript;
window.getCurrentAudioUrl = () => currentAudioUrl;

// ============================================================
// ============================================================
// PRE-LOADED CORE STEM LABS (100% Offline Standalone HTML5)
// ============================================================
const CORE_LABS = [
  {
    id: "core_ohms_law",
    isCore: true,
    subjectEn: "Physics",
    subjectAr: "الفيزياء",
    gradeEn: "Grade 8",
    gradeAr: "الصف الثامن",
    titleEn: "Ohm's Law Interactive Circuit",
    titleAr: "معمل قانون أوم للدوائر الكهربائية",
    descEn: "Discover electricity with a water-hose analogy: adjust battery push and resistance to watch current surge and the bulb shine bright.",
    descAr: "اكتشف سر الكهرباء بتشبيه بسيط: عدل قوة دفع البطارية والمقاومة وشوف إزاي التيار بيجري وينور المصباح بقوة.",
    engine: "SLIDER ENGINE (SANDBOXED)",
    formula: "I = V / R",
    accessibility: {
      adhd_steps: {
        en: [
          { title: "Step 1: Set Voltage", desc: "Slide the Voltage (V) to 12V and observe the battery potential." },
          { title: "Step 2: Adjust Resistor", desc: "Change Resistance (R) from 5Ω to 20Ω and watch the ammeter needle move." },
          { title: "Step 3: Track Current", desc: "Verify current I = V / R and notice how the circuit lightbulb responds." }
        ],
        ar: [
          { title: "الخطوة 1: زوّد زقة البطارية", desc: "حرّك المؤشر وزوّد الفولت لـ 12 وشوف البطارية وهي بتدفع التيار بقوة." },
          { title: "الخطوة 2: غيّر المقاومة", desc: "غيّر المقاومة من 5 لـ 20 وشوف إزاي مؤشر الأميتر هيتحرك." },
          { title: "الخطوة 3: راقب شدة التيار", desc: "شوف كل ما تقلل المقاومة اللمبة بتنور ألمع وأقوى إزاي!" }
        ]
      },
      bionic: {
        en: "<b>Ohm</b>'s <b>la</b>w <b>sta</b>tes <b>th</b>at <b>elec</b>tric <b>cur</b>rent <b>fl</b>ow <b>thr</b>ough <b>a</b> <b>cond</b>uctor <b>i</b>s <b>dire</b>ctly <b>prop</b>ortional <b>t</b>o <b>vol</b>tage <b>a</b>nd <b>inve</b>rsely <b>prop</b>ortional <b>t</b>o <b>resi</b>stance.",
        ar: "<b>ينص</b> <b>قانون</b> <b>أوم</b> على أن <b>شدة</b> <b>التيار</b> المار في <b>موصل</b> <b>تتناسب</b> <b>طردياً</b> مع <b>فرق</b> <b>الجهد</b> و<b>عكسياً</b> مع <b>المقاومة</b>."
      },
      kitchen: {
        en: "Take a standard 1.5V AA battery and a small LED torch bulb. Test how adding lead pencil graphite (a resistor) in series dims the LED bulb.",
        ar: "هات بطارية قلم صغيرة ولمبة ليد رفيعة، وجرب تمرر السلك في سن قلم رصاص خشب (جرافيت)، وشوف إزاي سن القلم هيعطل الكهرباء ويخلي نور اللمبة يضعف!"
      },
      voice_script: {
        en: "Hey champion! Picture electricity like water rushing through a hose: the battery is the pump pushing it forward, and the resistor is a clamp slowing it down. Crank up the voltage push, and the current rushes faster to light up the bulb bright!",
        ar: "أهلاً يا بطل! بص يا سيدي، تخيل الكهرباء زي مياه ماشية في خرطوم: البطارية هي الحنفية اللي بتزق، والمقاومة هي الحصى اللي بيعطلها.. كل ما تقوي الزقة (الفولت)، التيار يجري أسرع وتنور اللمبة أكتر.. شفت السهولة؟ وزي الفل!"
      },
      audio_url: {
        ar: "/api/audio/core_ohms_ar.mp3",
        en: "/api/audio/core_ohms_en.mp3"
      }
    },
    challenge: {
      qEn: "If you double the battery voltage from 6V to 12V while keeping resistance at 10Ω, what happens to current and electrical power?",
      qAr: "إذا ضاعفت جهد البطارية من 6 فولت إلى 12 فولت مع ثبات المقاومة عند 10 أوم، ماذا يحدث لشدة التيار والقدرة الكهربائية؟",
      hEn: "Look at I = V / R and P = V * I. Since R is fixed, doubling V doubles I.",
      hAr: "تذكر أن I = V / R والقدرة P = V * I. بما أن المقاومة ثابتة، فمضاعفة الجهد تضاعف التيار فوراً.",
      aEn: "Current doubles from 0.6A to 1.2A. Because Power = V * I, electrical power quadruples from 3.6W to 14.4W.",
      aAr: "تتضاعف شدة التيار من 0.6 إلى 1.2 أمبير. وبما أن القدرة = الجهد × التيار، فإن القدرة الكهربائية تتضاعف 4 مرات."
    },
    getHtml: function (isAr) {
      return `<!DOCTYPE html>
<html lang="${isAr ? 'ar' : 'en'}" dir="${isAr ? 'rtl' : 'ltr'}">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #FFFFFF; color: #0F172A; padding: 20px; text-align: center; }
  .card { max-width: 600px; margin: 0 auto; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
  h2 { font-size: 18px; font-weight: 800; color: #0F172A; margin-bottom: 4px; }
  .formula-badge { display: inline-block; background: #DCFCE7; color: #166534; font-weight: 800; font-size: 13px; padding: 3px 12px; border-radius: 9999px; margin-bottom: 20px; }
  .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
  .ctrl-box { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px; padding: 14px; text-align: ${isAr ? 'right' : 'left'}; }
  .ctrl-label { font-size: 12px; font-weight: 700; color: #475569; display: flex; justify-content: space-between; margin-bottom: 8px; }
  input[type="range"] { width: 100%; accent-color: #16A34A; cursor: pointer; }
  .meter-stage { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; margin-bottom: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
  .stat-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; }
  .stat-val { font-size: 20px; font-weight: 900; color: #16A34A; }
  .stat-lbl { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; }
  .bulb { width: 44px; height: 44px; border-radius: 50%; background: #CBD5E1; margin: 10px auto; transition: all 0.1s ease; border: 2px solid #94A3B8; }
</style>
</head>
<body>
<div class="card">
  <h2>${isAr ? 'معمل قانون أوم التفاعلي' : "Ohm's Law Interactive Circuit"}</h2>
  <span class="formula-badge">V = I × R</span>

  <div class="controls">
    <div class="ctrl-box">
      <div class="ctrl-label">
        <span>${isAr ? 'فرق الجهد (V)' : 'Voltage (V)'}</span>
        <span id="v-val">12 V</span>
      </div>
      <input type="range" id="v-slider" min="1" max="24" value="12" step="0.5" oninput="updateCircuit()">
    </div>

    <div class="ctrl-box">
      <div class="ctrl-label">
        <span>${isAr ? 'المقاومة (R)' : 'Resistance (R)'}</span>
        <span id="r-val">10 Ω</span>
      </div>
      <input type="range" id="r-slider" min="1" max="50" value="10" step="0.5" oninput="updateCircuit()">
    </div>
  </div>

  <div class="meter-stage">
    <div id="bulb" class="bulb"></div>
    <div style="font-size:12px; font-weight:700; color:#475569; margin-top:6px;">${isAr ? 'توهج المصباح ومؤشر التدفق' : 'Circuit Lamp Luminescence'}</div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-lbl">${isAr ? 'شدة التيار (I)' : 'Current (I)'}</div>
      <div class="stat-val" id="i-val">1.20 A</div>
    </div>
    <div class="stat-card">
      <div class="stat-lbl">${isAr ? 'القدرة (P)' : 'Power (P)'}</div>
      <div class="stat-val" id="p-val">14.4 W</div>
    </div>
    <div class="stat-card">
      <div class="stat-lbl">${isAr ? 'الحالة' : 'Circuit State'}</div>
      <div class="stat-val" id="state-val" style="font-size:14px; padding-top:6px; color:#0284C7;">${isAr ? 'آمنة' : 'Nominal'}</div>
    </div>
  </div>
</div>

<script>
function updateCircuit() {
  const v = parseFloat(document.getElementById('v-slider').value);
  const r = parseFloat(document.getElementById('r-slider').value);
  document.getElementById('v-val').textContent = v.toFixed(1) + ' V';
  document.getElementById('r-val').textContent = r.toFixed(1) + ' Ω';
  
  const i = v / r;
  const p = v * i;
  
  document.getElementById('i-val').textContent = i.toFixed(2) + ' A';
  document.getElementById('p-val').textContent = p.toFixed(1) + ' W';
  
  const bulb = document.getElementById('bulb');
  const brightness = Math.min(1, p / 30);
  bulb.style.background = 'rgb(' + Math.floor(255 * brightness) + ',' + Math.floor(220 * brightness) + ', 50)';
  bulb.style.boxShadow = '0 0 ' + Math.floor(brightness * 25) + 'px rgba(250, 204, 21, ' + brightness + ')';
}
updateCircuit();
<\/script>
</body>
</html>`;
    }
  },

  {
    id: "core_pendulum",
    isCore: true,
    subjectEn: "Physics",
    subjectAr: "الفيزياء",
    gradeEn: "Grade 7",
    gradeAr: "الصف السابع",
    titleEn: "Simple Harmonic Pendulum",
    titleAr: "معمل البندول التوافقي البسيط",
    descEn: "Playground physics in action: see why only string length and gravity control your swing, while mass changes nothing!",
    descAr: "فيزياء المرجوحة في ثواني: اكتشف ليه طول الحبل والجاذبية بس هما اللي بيتحكموا في التأرجح، والوزن ملوش أي تأثير!",
    engine: "SLIDER ENGINE (SANDBOXED)",
    formula: "T = 2π√(L / g)",
    accessibility: {
      adhd_steps: {
        en: [
          { title: "Step 1: Adjust String Length", desc: "Change string length (L) from 0.5m to 2.0m and watch the period slow down." },
          { title: "Step 2: Change Gravity", desc: "Select Moon (1.6 m/s²) or Jupiter (24.8 m/s²) to test gravitational acceleration." },
          { title: "Step 3: Measure Period", desc: "Verify that mass does NOT affect oscillation period in harmonic motion." }
        ],
        ar: [
          { title: "الخطوة 1: جرّب طول الحبل", desc: "طوّل وقصّر في حبل المرجوحة وشوف التأرجح بيحصل فيه إيه." },
          { title: "الخطوة 2: سافر للقمر والمشتري", desc: "غيّر الجاذبية للقمر وشوف البندول وهو بيتحرك براحة تامة." },
          { title: "الخطوة 3: غيّر الوزن واتأكد", desc: "زوّد الثقل وهتلاقي سرعة اللفة زي ما هي مابتتغيرش خالص!" }
        ]
      },
      bionic: {
        en: "<b>Th</b>e <b>peri</b>od <b>o</b>f <b>a</b> <b>sim</b>ple <b>pend</b>ulum <b>dep</b>ends <b>on</b>ly <b>o</b>n <b>i</b>ts <b>len</b>gth <b>a</b>nd <b>loc</b>al <b>grav</b>ity, <b>indep</b>endent <b>o</b>f <b>i</b>ts <b>ma</b>ss.",
        ar: "<b>يعتمد</b> <b>الزمن</b> <b>الدوري</b> للبندول البسيط فقط على <b>طول</b> <b>الخيط</b> و<b>تسارع</b> <b>الجاذبية</b> ودون أي <b>تأثير</b> للكتلة."
      },
      kitchen: {
        en: "Tie a key or small spoon to a 1-meter sewing thread. Suspend it from a door handle and time 10 full swings with a phone stopwatch.",
        ar: "اربط مفتاح شقة أو ملعقة صغيرة في طرف خيط خياطة طوله متر، وثبته في أكرة الباب، وسيبه يتمرجح وقيس وقت 10 لفات بساعة الموبايل.. هتنبهر!"
      },
      voice_script: {
        en: "Ever been on a playground swing? A pendulum works the exact same way! Surprise: your weight doesn't change your swing speed at all. It's all about rope length—longer rope gives a gentle, slow glide, while a short string swings lightning fast!",
        ar: "عارف المرجوحة يا بطل؟ البندول زيك وإنت بتتمرجح بالظبط! والمفاجأة الحلوة إن وزنك مش هيخلي المرجوحة أسرع ولا أبطأ، السر كله في طول الحبل: حبل طويل يمرجحك براحة وهدوء، وحبل قصير يطيرك بسرعة صاروخية!"
      },
      audio_url: {
        ar: "/api/audio/core_pendulum_ar.mp3",
        en: "/api/audio/core_pendulum_en.mp3"
      }
    },
    challenge: {
      qEn: "If you take a pendulum with period 2.0s on Earth (g = 9.8) to the Moon (g = 1.6), what happens to its swing period?",
      qAr: "إذا أخذت بندولاً يهتز بزمن دوري 2 ثانية على الأرض إلى سطح القمر (g = 1.6)، ماذا يحدث لزمنه الدوري؟",
      hEn: "Notice that g is in the denominator under the square root in T = 2π√(L/g). Smaller g means larger T.",
      hAr: "لاحظ أن g تقع في المقام تحت الجذر. انخفاض الجاذبية يعني كبر الزمن الدوري وبطء الاهتزاز.",
      aEn: "The period increases from 2.0s to approximately 4.9s. The pendulum swings much more slowly in the Moon's weaker gravity.",
      aAr: "يزداد الزمن الدوري من 2 ثانية إلى قرابة 4.9 ثانية، ويتأرجح البندول ببطء شديد على القمر لضعف الجاذبية."
    },
    getHtml: function (isAr) {
      return `<!DOCTYPE html>
<html lang="${isAr ? 'ar' : 'en'}" dir="${isAr ? 'rtl' : 'ltr'}">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #FFFFFF; color: #0F172A; padding: 20px; text-align: center; }
  .card { max-width: 600px; margin: 0 auto; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; }
  h2 { font-size: 18px; font-weight: 800; color: #0F172A; margin-bottom: 4px; }
  .formula-badge { display: inline-block; background: #E0F2FE; color: #0369A1; font-weight: 800; font-size: 13px; padding: 3px 12px; border-radius: 9999px; margin-bottom: 16px; }
  .canvas-stage { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; margin-bottom: 20px; overflow: hidden; }
  .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 18px; text-align: ${isAr ? 'right' : 'left'}; }
  .ctrl-box { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 12px; }
  .ctrl-lbl { font-size: 12px; font-weight: 700; color: #475569; display: flex; justify-content: space-between; margin-bottom: 6px; }
  input[type="range"] { width: 100%; accent-color: #0284C7; cursor: pointer; }
  .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .stat-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; }
  .stat-val { font-size: 22px; font-weight: 900; color: #0284C7; }
  .stat-lbl { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; }
</style>
</head>
<body>
<div class="card">
  <h2>${isAr ? 'معمل البندول التوافقي البسيط' : 'Simple Harmonic Pendulum'}</h2>
  <span class="formula-badge">T = 2π√(L / g)</span>

  <div class="canvas-stage">
    <canvas id="p-canvas" width="550" height="220"></canvas>
  </div>

  <div class="controls">
    <div class="ctrl-box">
      <div class="ctrl-lbl">
        <span>${isAr ? 'طول الخيط (L)' : 'String Length (L)'}</span>
        <span id="l-val">1.0 m</span>
      </div>
      <input type="range" id="l-slider" min="0.2" max="2.0" value="1.0" step="0.05" oninput="updatePendulum()">
    </div>

    <div class="ctrl-box">
      <div class="ctrl-lbl">
        <span>${isAr ? 'تسارع الجاذبية (g)' : 'Gravity (g)'}</span>
        <span id="g-val">9.8 m/s²</span>
      </div>
      <input type="range" id="g-slider" min="1.6" max="25" value="9.8" step="0.2" oninput="updatePendulum()">
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-lbl">${isAr ? 'الزمن الدوري (T)' : 'Oscillation Period (T)'}</div>
      <div class="stat-val" id="t-val">2.01 s</div>
    </div>
    <div class="stat-card">
      <div class="stat-lbl">${isAr ? 'التردد (f = 1/T)' : 'Frequency (f)'}</div>
      <div class="stat-val" id="f-val">0.50 Hz</div>
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById('p-canvas');
const ctx = canvas.getContext('2d');
let l = 1.0;
let g = 9.8;
let time = 0;

function updatePendulum() {
  l = parseFloat(document.getElementById('l-slider').value);
  g = parseFloat(document.getElementById('g-slider').value);
  document.getElementById('l-val').textContent = l.toFixed(2) + ' m';
  document.getElementById('g-val').textContent = g.toFixed(1) + ' m/s²';
  
  const T = 2 * Math.PI * Math.sqrt(l / g);
  document.getElementById('t-val').textContent = T.toFixed(2) + ' s';
  document.getElementById('f-val').textContent = (1 / T).toFixed(2) + ' Hz';
}

function animate() {
  time += 0.03;
  const T = 2 * Math.PI * Math.sqrt(l / g);
  const curAngle = 0.45 * Math.cos((2 * Math.PI / T) * time);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const originX = canvas.width / 2;
  const originY = 20;
  const pixelLen = 60 + l * 60;
  const bobX = originX + pixelLen * Math.sin(curAngle);
  const bobY = originY + pixelLen * Math.cos(curAngle);

  // Pivot support
  ctx.fillStyle = '#0F172A';
  ctx.fillRect(originX - 30, originY - 6, 60, 6);

  // String
  ctx.beginPath();
  ctx.moveTo(originX, originY);
  ctx.lineTo(bobX, bobY);
  ctx.strokeStyle = '#64748B';
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // Bob
  ctx.beginPath();
  ctx.arc(bobX, bobY, 14, 0, Math.PI * 2);
  ctx.fillStyle = '#0284C7';
  ctx.fill();
  ctx.strokeStyle = '#0F172A';
  ctx.lineWidth = 2;
  ctx.stroke();

  requestAnimationFrame(animate);
}
updatePendulum();
animate();
<\/script>
</body>
</html>`;
    }
  },

  {
    id: "core_binary_search",
    isCore: true,
    subjectEn: "Computer Science",
    subjectAr: "علوم الحاسب والرياضيات",
    gradeEn: "Grade 9",
    gradeAr: "الصف التاسع",
    titleEn: "Binary Search Visualizer",
    titleAr: "معمل خوارزمية البحث الثنائي",
    descEn: "The ultimate guessing trick: chop the search area in half each step to find any hidden number in record time!",
    descAr: "حيلة الفوازير الذكية: اقسم منطقة البحث نصين في كل خطوة عشان تلاقي أي رقم مستخبي في أسرع وقت ممكن!",
    engine: "STEPPER ENGINE (SANDBOXED)",
    formula: "Steps ≤ ⌈log₂(N)⌉",
    accessibility: {
      adhd_steps: {
        en: [
          { title: "Step 1: Pick Target Value", desc: "Select a target number to find in the 16-element sorted list." },
          { title: "Step 2: Inspect Midpoint", desc: "Compare target with mid element; discard the unneeded half immediately." },
          { title: "Step 3: Halve the Interval", desc: "Repeat until target is isolated in at most 4 steps." }
        ],
        ar: [
          { title: "الخطوة 1: اختار الرقم المستخبي", desc: "حدد الرقم اللي نفسك تدور عليه وسط الأرقام المترتبة." },
          { title: "الخطوة 2: اضرب في النص واقسم", desc: "قارن بالرقم اللي في النص واستبعد النص اللي ملوش لازمة علطول." },
          { title: "الخطوة 3: كرر واوصل للهدف", desc: "كرر نفس الحركة وهتوصل للرقم في 4 خطوات بس بالكتير!" }
        ]
      },
      bionic: {
        en: "<b>Bin</b>ary <b>sea</b>rch <b>fin</b>ds <b>th</b>e <b>posi</b>tion <b>o</b>f <b>a</b> <b>tar</b>get <b>val</b>ue <b>with</b>in <b>a</b> <b>sor</b>ted <b>arr</b>ay <b>b</b>y <b>repe</b>atedly <b>divi</b>ding <b>th</b>e <b>sea</b>rch <b>int</b>erval <b>i</b>n <b>ha</b>lf.",
        ar: "<b>يعمل</b> <b>البحث</b> <b>الثنائي</b> على <b>إيجاد</b> <b>العنصر</b> المطلوب في <b>مصفوفة</b> <b>مرتبة</b> عن طريق <b>تنصيف</b> <b>مجال</b> <b>البحث</b> تكرارياً."
      },
      kitchen: {
        en: "Take an open dictionary or phone book with 500 pages. Open exactly in the middle to find a name; if it starts with 'M' and you want 'S', discard the entire first half.",
        ar: "افتح قاموس أو كتاب كبير من 500 صفحة في النص بالظبط؛ لو الكلمة بحرف الميم وإنت عايز الياء، ارمي النص الأولاني كله وكمل في النص التاني!"
      },
      voice_script: {
        en: "Imagine playing a secret number guessing game from 1 to 100. Instead of guessing one by one, cut straight to the middle! Binary search is pure superpower: it chops away half the numbers in every single guess to find the prize in a flash!",
        ar: "لو بتلعب لعبة 'فزورة رقم' من 1 لـ 100، بدل ما تقعد تجرب رقم رقم وتزهق، ارمي نص الأرقام وافتح من النص على 50 علطول! البحث الثنائي ذكي جداً: بيقسم اللعبة نصين في كل حركة عشان يوصل للرقم الصح في رمشة عين ومن غير أي مجهود!"
      },
      audio_url: {
        ar: "/api/audio/core_binary_ar.mp3",
        en: "/api/audio/core_binary_en.mp3"
      }
    },
    challenge: {
      qEn: "If an array has 1,024 sorted numbers, what is the maximum number of comparisons binary search needs to find any item?",
      qAr: "إذا كانت المصفوفة تحتوي على 1,024 عنصراً مرتباً، ما هو أقصى عدد مقارنات يحتاجه البحث الثنائي لإيجاد أي عنصر؟",
      hEn: "Think about powers of 2. 2^10 = 1024.",
      hAr: "احسب قوى العدد 2. كم 2 مضروبة في نفسها لتعطي 1024؟",
      aEn: "Exactly 10 comparisons (log2(1024) = 10). Linear search might take 1,024 steps, proving O(log N) algorithmic efficiency.",
      aAr: "10 مقارنات فقط كحد أقصى (log2(1024) = 10)، بينما قد يتطلب البحث الخطي 1,024 مقارنة."
    },
    getHtml: function (isAr) {
      return `<!DOCTYPE html>
<html lang="${isAr ? 'ar' : 'en'}" dir="${isAr ? 'rtl' : 'ltr'}">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #FFFFFF; color: #0F172A; padding: 20px; text-align: center; }
  .card { max-width: 600px; margin: 0 auto; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; }
  h2 { font-size: 18px; font-weight: 800; color: #0F172A; margin-bottom: 4px; }
  .formula-badge { display: inline-block; background: #FEF3C7; color: #92400E; font-weight: 800; font-size: 13px; padding: 3px 12px; border-radius: 9999px; margin-bottom: 20px; }
  .array-container { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; margin: 20px 0; }
  .num-box { width: 32px; height: 38px; border-radius: 6px; background: #FFFFFF; border: 1px solid #CBD5E1; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 800; transition: all 0.2s; }
  .num-box.discarded { background: #F1F5F9; color: #94A3B8; border-color: #E2E8F0; opacity: 0.4; }
  .num-box.mid { background: #22C55E; color: #FFFFFF; border-color: #16A34A; transform: scale(1.1); }
  .btn-step { background: #0F172A; color: #FFFFFF; border: none; border-radius: 9999px; padding: 10px 22px; font-size: 13px; font-weight: 700; cursor: pointer; margin: 6px; }
  .btn-step:hover { background: #334155; }
  .status-text { font-size: 14px; font-weight: 700; color: #334155; min-height: 24px; margin-top: 10px; }
</style>
</head>
<body>
<div class="card">
  <h2>${isAr ? 'معمل خوارزمية البحث الثنائي' : 'Binary Search Visualizer'}</h2>
  <span class="formula-badge">O(log₂ N) Complexity</span>

  <div style="margin-bottom: 12px;">
    <label style="font-size:12px; font-weight:700; color:#475569;">${isAr ? 'اختر الرقم المطلوب البحث عنه:' : 'Select Target Number:'} </label>
    <select id="target-sel" onchange="resetSearch()" style="padding:4px 8px; border-radius:6px; border:1px solid #CBD5E1; font-weight:700;">
      <option value="45" selected>45</option>
      <option value="12">12</option>
      <option value="78">78</option>
      <option value="99">99</option>
      <option value="2">2</option>
    </select>
  </div>

  <div class="array-container" id="array-boxes"></div>

  <div>
    <button class="btn-step" onclick="nextStep()">${isAr ? 'الخطوة التالية (تنصيف)' : 'Next Step (Halve)'}</button>
    <button class="btn-step" style="background:#E2E8F0; color:#0F172A;" onclick="resetSearch()">${isAr ? 'إعادة ضبط' : 'Reset'}</button>
  </div>

  <div class="status-text" id="status-msg">${isAr ? 'جاهز للبدء. اضغط الخطوة التالية.' : 'Ready. Click Next Step to search.'}</div>
</div>

<script>
const arr = [2, 5, 8, 12, 16, 23, 38, 45, 56, 67, 78, 82, 89, 91, 95, 99];
let low = 0;
let high = arr.length - 1;
let stepCount = 0;
let done = false;

function renderArray(mid = -1) {
  const container = document.getElementById('array-boxes');
  container.innerHTML = '';
  arr.forEach((val, idx) => {
    const box = document.createElement('div');
    box.className = 'num-box';
    box.textContent = val;
    if (idx < low || idx > high) box.classList.add('discarded');
    if (idx === mid) box.classList.add('mid');
    container.appendChild(box);
  });
}

function resetSearch() {
  low = 0;
  high = arr.length - 1;
  stepCount = 0;
  done = false;
  renderArray();
  document.getElementById('status-msg').textContent = "${isAr ? 'جاهز للبدء. اضغط الخطوة التالية.' : 'Ready. Click Next Step to search.'}";
}

function nextStep() {
  if (done || low > high) return;
  stepCount++;
  const target = parseInt(document.getElementById('target-sel').value, 10);
  const mid = Math.floor((low + high) / 2);
  renderArray(mid);

  if (arr[mid] === target) {
    document.getElementById('status-msg').textContent = "${isAr ? 'تم العثور على الرقم!' : 'Target Found!'} " + target + " ${isAr ? 'في' : 'in'} " + stepCount + " ${isAr ? 'خطوات.' : 'steps.'}";
    done = true;
  } else if (arr[mid] < target) {
    document.getElementById('status-msg').textContent = "${isAr ? 'المنتصف' : 'Mid'} (" + arr[mid] + ") < " + target + ". ${isAr ? 'استبعاد النصف الأيسر.' : 'Discarding left half.'}";
    low = mid + 1;
  } else {
    document.getElementById('status-msg').textContent = "${isAr ? 'المنتصف' : 'Mid'} (" + arr[mid] + ") > " + target + ". ${isAr ? 'استبعاد النصف الأيمن.' : 'Discarding right half.'}";
    high = mid - 1;
  }
}
resetSearch();
<\/script>
</body>
</html>`;
    }
  },

  {
    id: "core_ph_scale",
    isCore: true,
    subjectEn: "Chemistry",
    subjectAr: "الكيمياء",
    gradeEn: "Grade 8",
    gradeAr: "الصف الثامن",
    titleEn: "Acids, Bases & pH Scale",
    titleAr: "معمل مقياس الرقم الهيدروجيني (pH)",
    descEn: "Meet the liquid superpower meter: test sour lemons, soothing water, and slippery soaps on the 0 to 14 scale!",
    descAr: "ميزان قوة السوائل العجيب: اختبر لسعة الليمون الحامض ونعومة الصابون وشوف نقطة تعادل الماء النقي!",
    engine: "SLIDER ENGINE (SANDBOXED)",
    formula: "pH = -log₁₀[H⁺]",
    accessibility: {
      adhd_steps: {
        en: [
          { title: "Step 1: Acid Range (0 - 6)", desc: "Slide left to see red/orange color shift and dominant H+ hydrogen ions." },
          { title: "Step 2: Neutral Point (7.0)", desc: "Reach pH 7 for pure distilled water with equal balance of H+ and OH- ions." },
          { title: "Step 3: Base Range (8 - 14)", desc: "Slide right to observe blue/violet hue representing alkaline hydroxide solutions." }
        ],
        ar: [
          { title: "الخطوة 1: روح لسكة الليمون (حمضي)", desc: "حرّك المؤشر للشمال وشوف اللون الأحمر ولسعة الأحماض." },
          { title: "الخطوة 2: اقف عند مياه الشرب (متعادل)", desc: "اقف عند رقم 7 لمياه شرب صافية متوازنة في النص بالظبط." },
          { title: "الخطوة 3: روح لسكة الصابون (قلوي)", desc: "حرّك لليمين وشوف اللون الأزرق والموف بتاع المنظفات والصابون." }
        ]
      },
      bionic: {
        en: "<b>Th</b>e <b>p</b>H <b>sca</b>le <b>meas</b>ures <b>h</b>ow <b>aci</b>dic <b>o</b>r <b>bas</b>ic <b>a</b> <b>solu</b>tion <b>i</b>s, <b>rang</b>ing <b>fr</b>om <b>0</b> <b>t</b>o <b>14</b>, <b>wi</b>th <b>7</b> <b>bei</b>ng <b>neut</b>ral.",
        ar: "<b>يقيس</b> <b>مقياس</b> <b>الرقم</b> <b>الهيدروجيني</b> درجة <b>حموضة</b> أو <b>قلوية</b> المحاليل من 0 إلى 14 حيث يمثل 7 <b>نقطة</b> <b>التعادل</b>."
      },
      kitchen: {
        en: "Boil red cabbage in water to extract purple natural indicator fluid. Add lemon juice to turn it bright red, and baking soda to turn it teal blue.",
        ar: "اغلي شوية ورق كرنب أحمر في مياه وخد المية البنفسجي، حط عليها عصرة ليمون هتلاقيها قلبت أحمر علطول، وحط عليها شوية كربوناتو هتلاقيها قلبت أزرق ساحر!"
      },
      voice_script: {
        en: "The pH scale is nature's flavor and power meter! Super sour and zesty like lemon juice sits low under 7, slippery and soapy sits high above 7, and pure water rests right in the sweet spot at 7—peaceful and balanced!",
        ar: "الـ pH ده يا بطل ميزان طعم وقوة السوائل! لو حامض ولاسع زي الليمون يبقى رقمه قليل تحت 7، ولو ناعم ومزحلق زي الصابون يبقى فوق 7، ومياه الشرب الصافية في النص 7 تماماً.. مسالمة ومتعادلة وزي الفل!"
      },
      audio_url: {
        ar: "/api/audio/core_ph_ar.mp3",
        en: "/api/audio/core_ph_en.mp3"
      }
    },
    challenge: {
      qEn: "If solution A has pH 4 and solution B has pH 6, how many times more acidic is solution A than solution B?",
      qAr: "إذا كان المحلول (أ) برقم هيدروجيني 4 والمحلول (ب) برقم هيدروجيني 6، كم مرة تزيد حموضة (أ) عن (ب)؟",
      hEn: "Remember that the pH scale is logarithmic (base 10). Each unit change represents a 10-fold change in [H+].",
      hAr: "تذكر أن مقياس pH مقياس لوغاريتمي عشري. كل درجة تمثل تغيراً بمقدار 10 أضعاف في تركيز أيونات H+.",
      aEn: "Solution A is 100 times more acidic (10^(6 - 4) = 10^2 = 100 times higher H+ ion concentration).",
      aAr: "المحلول (أ) أكثر حموضة بمقدار 100 مرة (10 مرفوعة للأس 2 = 100 ضعف في تركيز أيونات H+)."
    },
    getHtml: function (isAr) {
      return `<!DOCTYPE html>
<html lang="${isAr ? 'ar' : 'en'}" dir="${isAr ? 'rtl' : 'ltr'}">
<head>
<meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  body { background: #FFFFFF; color: #0F172A; padding: 20px; text-align: center; }
  .card { max-width: 600px; margin: 0 auto; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; }
  h2 { font-size: 18px; font-weight: 800; color: #0F172A; margin-bottom: 4px; }
  .formula-badge { display: inline-block; background: #F3E8FF; color: #7E22CE; font-weight: 800; font-size: 13px; padding: 3px 12px; border-radius: 9999px; margin-bottom: 16px; }
  .beaker-stage { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 20px; margin-bottom: 20px; display: flex; flex-direction: column; align-items: center; }
  .beaker { width: 100px; height: 130px; border: 3px solid #64748B; border-top: none; border-radius: 0 0 16px 16px; position: relative; overflow: hidden; background: #F8FAFC; margin-bottom: 12px; }
  .liquid { position: absolute; bottom: 0; left: 0; right: 0; height: 75%; transition: background-color 0.2s ease; }
  .controls { margin-bottom: 20px; text-align: ${isAr ? 'right' : 'left'}; }
  .ctrl-box { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px; }
  .ctrl-lbl { font-size: 13px; font-weight: 700; color: #475569; display: flex; justify-content: space-between; margin-bottom: 8px; }
  input[type="range"] { width: 100%; accent-color: #7E22CE; cursor: pointer; }
  .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .stat-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; }
  .stat-val { font-size: 20px; font-weight: 900; }
  .stat-lbl { font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; }
</style>
</head>
<body>
<div class="card">
  <h2>${isAr ? 'معمل مقياس الرقم الهيدروجيني (pH)' : 'Acids, Bases & pH Scale'}</h2>
  <span class="formula-badge">pH = -log₁₀[H⁺]</span>

  <div class="beaker-stage">
    <div class="beaker">
      <div class="liquid" id="liquid"></div>
    </div>
    <div style="font-size:15px; font-weight:800;" id="substance-name">${isAr ? 'ماء نقي (متعادل)' : 'Pure Water (Neutral)'}</div>
  </div>

  <div class="controls">
    <div class="ctrl-box">
      <div class="ctrl-lbl">
        <span>${isAr ? 'قيمة الرقم الهيدروجيني (pH):' : 'pH Value:'}</span>
        <span id="ph-val" style="font-weight:900; font-size:15px; color:#7E22CE;">7.0</span>
      </div>
      <input type="range" id="ph-slider" min="0" max="14" value="7.0" step="0.1" oninput="updatePH()">
    </div>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-lbl">${isAr ? 'تصنيف المحلول' : 'Solution Nature'}</div>
      <div class="stat-val" id="nature-val" style="color:#16A34A;">${isAr ? 'متعادل' : 'Neutral'}</div>
    </div>
    <div class="stat-card">
      <div class="stat-lbl">${isAr ? 'الأيون السائد' : 'Dominant Ion'}</div>
      <div class="stat-val" id="ion-val" style="font-size:15px; padding-top:4px;">[H⁺] = [OH⁻]</div>
    </div>
  </div>
</div>

<script>
function getPHColor(ph) {
  if (ph < 3) return '#EF4444';
  if (ph < 6) return '#F97316';
  if (ph <= 7.5) return '#22C55E';
  if (ph < 11) return '#0284C7';
  return '#7E22CE';
}

function updatePH() {
  const ph = parseFloat(document.getElementById('ph-slider').value);
  document.getElementById('ph-val').textContent = ph.toFixed(1);
  const color = getPHColor(ph);
  document.getElementById('liquid').style.backgroundColor = color;
  
  const nature = document.getElementById('nature-val');
  const ion = document.getElementById('ion-val');
  const sub = document.getElementById('substance-name');

  if (ph < 6.8) {
    nature.textContent = "${isAr ? 'حمضي' : 'Acidic'}";
    nature.style.color = '#EF4444';
    ion.textContent = "[H⁺] > [OH⁻]";
    sub.textContent = ph < 3 ? "${isAr ? 'عصير ليمون / حمض معدة' : 'Gastric Acid / Lemon'}" : "${isAr ? 'خل / قهوة سوداء' : 'Vinegar / Coffee'}";
  } else if (ph > 7.4) {
    nature.textContent = "${isAr ? 'قلوي (قاعدي)' : 'Alkaline (Base)'}";
    nature.style.color = '#7E22CE';
    ion.textContent = "[OH⁻] > [H⁺]";
    sub.textContent = ph > 11 ? "${isAr ? 'مبيض منزلي / منظف أفران' : 'Bleach / Drain Cleaner'}" : "${isAr ? 'بيكربونات الصودا / حليب المغنيسيا' : 'Baking Soda / Soap'}";
  } else {
    nature.textContent = "${isAr ? 'متعادل' : 'Neutral'}";
    nature.style.color = '#16A34A';
    ion.textContent = "[H⁺] = [OH⁻]";
    sub.textContent = "${isAr ? 'ماء مقطر نقي' : 'Pure Distilled Water'}";
  }
}
updatePH();
<\/script>
</body>
</html>`;
    }
  }
];

// ============================================================

window.CORE_LABS = CORE_LABS;
// BILINGUAL LOCALIZATION DICTIONARY
// ============================================================
const I18N = {
  en: {
    lang: "en",
    dir: "ltr",
    pageTitle: "LuminaLab Swarm | Enterprise Adaptive STEM Labs",
    langBtn: "العربية",
    statusMock: "Deterministic Mock",
    statusCloud: "AWS Bedrock Active",

    // Primary Environment Modes
    modeOnline: "Online Studio",
    modeOffline: "Offline Vault",

    // Navigation Tabs
    tabStudio: "Curriculum Studio",
    tabLab: "Simulation Lab",
    tabSensory: "Sensory Suite",
    tabMastery: "Mastery & Voice",
    tabImpact: "Impact Ledger",
    tabVault: "Offline Vault",

    // Banners
    badgeOnline: "AWS BEDROCK MULTI-AGENT SWARM",
    descOnline: "<strong>Connected AI Synthesis Mode:</strong> Autonomous 6-agent Strands swarm parses raw textbook curricula, executes deterministic mathematical guards, and outputs sandboxed zero-dependency simulations.",
    badgeOffline: "100% OFFLINE LOCAL VAULT",
    descOffline: "<strong>Zero-CDN Airplane Mode:</strong> All labs are self-contained micro-engines (< 200 KB) stored directly in browser local storage. Operates flawlessly with zero internet, zero CDN dependencies, and zero tracking.",

    // Studio View
    heroBadgeStudio: "Autonomous Pedagogical Swarm",
    heroTitleStudio: "Autonomous STEM Lab Generation for <span>Every Student</span>.",
    heroSubStudio: "Convert unstructured curriculum passages into interactive, mathematically verified micro-labs with instant sensory and cognitive adaptations.",
    studioFormTitle: "Curriculum Passage & Target Parameters",
    studioFormSub: "Specify subject parameters to initialize the multi-agent pedagogical swarm",
    btnSample: "Load Reference Sample",
    lblSubject: "Academic Subject",
    lblGrade: "Target Student Grade",
    lblTopic: "Experiment Topic",
    lblText: "Curriculum Lesson Passage",
    btnRun: "Run Pedagogical Swarm",
    guardNotice: "Deterministic Sandbox Guard active on all outputs",
    readyToSend: "Ready to transmit",
    charUnit: "characters",
    pipelineTitle: "Strands multi-agent pipeline executing...",

    // Sample Data
    sampleSubject: "Physics",
    sampleTopic: "Ohm's Law",
    sampleGrade: "8",
    sampleText: "Ohm's law states that the current through a conductor between two points is directly proportional to the voltage across the two points and inversely proportional to resistance. The formula is V = I * R where V is voltage, I is current, and R is resistance.",

    // Lab Player View
    heroBadgeLab: "Zero-CDN Standalone Simulator",
    heroTitleLab: "Self-Contained Interactive <span>Lab Player</span>.",
    heroSubLab: "Pure vanilla HTML/CSS/JS simulation running entirely client-side without any third-party dependencies or external CDN tracking.",
    emptyLabH: "No Active Simulation",
    emptyLabP: "Execute the Curriculum Studio to synthesize and verify an interactive lab.",
    btnGotoStudio: "Go to Curriculum Studio",
    btnReloadLab: "Reset Simulator",
    btnSaveVault: "Save to Offline Vault",
    btnDownloadLab: "Download Offline Lab",
    saveToast: "Saved to Offline Vault!",

    // Sensory Suite View
    heroBadgeSensory: "Neurodiverse Pedagogical Adaptation",
    heroTitleSensory: "Comprehensive Sensory <span>Adaptation Suite</span>.",
    heroSubSensory: "Neural-inclusive artifacts: 3-step executive chunking for ADHD, Bionic Reading eye-guidance for Dyslexia, and tactile home experiment protocol.",
    emptySensoryH: "No Sensory Data Available",
    emptySensoryP: "Trigger the swarm in Curriculum Studio to generate sensory adaptation protocols.",
    secAdhdTitle: "ADHD Micro-Focus Protocol (3-Step Chunking)",
    secAdhdSub: "Breaks cognitive load into 3 self-contained, sensory-grounded execution phases",
    secBionicTitle: "Bionic Visual Guidance (Eye-Fixation Anchors)",
    secBionicSub: "Artificial fixation points on word stems to anchor reading trajectory for dyslexic learners",
    secKitchenTitle: "Tactile Kitchen Lab Protocol",
    secKitchenSub: "Reinforces abstract principles with everyday physical household items",

    // Mastery View
    heroBadgeMastery: "AWS Polly Synthesis & Socratic Inquiry",
    heroTitleMastery: "Socratic Reasoning & <span>Voice Companion</span>.",
    heroSubMastery: "High-order thinking questions designed to test principle transfer, coupled with studio-grade synthesized audio narration.",
    emptyMasteryH: "No Challenge or Audio Data Available",
    emptyMasteryP: "Trigger the swarm in Curriculum Studio to synthesize audio companion dialogue.",
    secVoiceTitle: "Studio Voice Companion & Narration",
    secVoiceSub: "Auditory pedagogical narration generated specifically for multi-sensory and ADHD learning",
    btnDownloadAudio: "Download MP3",
    lblTranscriptTitle: "Read-Along Narration Script",
    voiceEnginePolly: "AWS Polly Neural 🎙️",
    voiceEngineNative: "Offline Browser Voice 🔊",
    secSocraticTitle: "Socratic Reasoning Challenge",
    secSocraticSub: "Non-trivial conceptual transfer question challenging mechanical memorization",
    socraticPromptBadge: "INQUIRY CHALLENGE",
    lblHypothesis: "Student Scientific Hypothesis",
    hypothesisPh: "Formulate your explanation based on the simulation observations...",
    btnCheck: "Submit Hypothesis",
    btnHintReveal: "Reveal Pedagogical Hint",
    btnHintHide: "Hide Pedagogical Hint",
    btnAnswerReveal: "Reveal Model Explanation",
    btnAnswerHide: "Hide Model Explanation",
    lblHintBadge: "Pedagogical Guiding Hint",
    lblAnswerBadge: "Verified Model Explanation",

    // Impact Ledger View
    heroBadgeImpact: "Amazon DynamoDB Audit Ledger",
    heroTitleImpact: "Educational Impact & <span>DynamoDB Ledger</span>.",
    heroSubImpact: "Deterministic verification metrics: cognitive load reduction, bundle size optimization, and tamper-evident DynamoDB audit trails.",
    statGrade: "Grade Reading Reduction",
    statCog: "Cognitive Load Reduction",
    statSize: "Micro-Lab Bundle Size",
    statOffline: "Offline Zero-CDN Readiness",
    secCloudStatsTitle: "Cloud Ledger Aggregates & System Health",
    secCloudStatsSub: "Live DynamoDB ledger transactions verified across AWS ME-SOUTH-1",
    btnRefresh: "Refresh Cloud Ledger",
    lblAuditSessions: "Total Registered Sessions:",
    lblAuditReduction: "Average Complexity Reduction:",
    lblAuditOffline: "Zero-CDN Ready Simulations:",

    // Vault Library View
    heroBadgeVault: "Local Offline Library",
    heroTitleVault: "Curated Standalone <span>STEM Labs</span>.",
    heroSubVault: "Instant execution in isolated sandboxes. Includes core foundational STEM micro-labs and your custom saved simulations from the Cloud Studio.",
    txtFilterAll: "All Labs",
    txtFilterCore: "Core STEM Labs",
    txtFilterSaved: "Saved from Cloud",
    btnLaunchVault: "Launch Lab",
    btnDeleteVault: "Delete",
    vaultTagCore: "Core STEM",
    vaultTagSaved: "Saved from Cloud",

    // Runtime Player View
    txtBackVault: "← Back to Vault Library",
    runtimeBadge: "Offline Standalone",
    btnDownloadRuntime: "Download Standalone .html",
    txtRtAdhd: "ADHD Steps",
    txtRtBionic: "Bionic Reading",
    txtRtKitchen: "Home Experiment",
    txtRtSocratic: "Socratic Challenge",
    lblRtHintBadge: "Guiding Hint",
    lblRtAnswerBadge: "Verified Explanation",

    grades: [
      { v: "6", l: "Grade 6 — Middle School" },
      { v: "7", l: "Grade 7 — Middle School" },
      { v: "8", l: "Grade 8 — Middle School" },
      { v: "9", l: "Grade 9 — High School" },
      { v: "10", l: "Grade 10 — High School" },
      { v: "11", l: "Grade 11 — High School" },
      { v: "12", l: "Grade 12 — High School" }
    ],

    pipelineSteps: [
      "Agent 1A: Deconstruct lesson concept & define mastery objectives",
      "Agent 1B: Match mathematical simulation engine & AST bounds",
      "Agent 2A: Synthesize self-contained HTML5/SVG simulation micro-lab",
      "Agent 2B: Execute strict Sandbox Guard and deterministic AST verification",
      "Agent 3A: Generate ADHD chunks, Bionic anchors, & Socratic challenge",
      "AWS Ledger: Commit deterministic audit metrics to DynamoDB & S3"
    ]
  },

  ar: {
    lang: "ar",
    dir: "rtl",
    pageTitle: "LuminaLab Swarm | مختبرات STEM التكيفية والخزنة المحلية",
    langBtn: "English",
    statusMock: "المحاكاة المحلية",
    statusCloud: "سحابة AWS نشطة",

    // Primary Environment Modes
    modeOnline: "استوديو السحابة",
    modeOffline: "الخزنة المحلية",

    // Navigation Tabs
    tabStudio: "استوديو المناهج",
    tabLab: "مشغل المختبر",
    tabSensory: "التنظيم الحسي",
    tabMastery: "الصوت والإتقان",
    tabImpact: "سجل الأثر",
    tabVault: "الخزنة المحلية",

    // Banners
    badgeOnline: "سرب وكلاء AWS BEDROCK السحابي",
    descOnline: "<strong>وضع التوليد السحابي الذكي:</strong> سرب مستقل من 6 وكلاء Strands يحلل نصوص المناهج ويفحص الأمان الحتمي ويولد محاكيات تفاعلية مستقلة بدون أي اتصالات خارجية.",
    badgeOffline: "خزنة المعامل المستقلة 100% دون إنترنت",
    descOffline: "<strong>استقلالية تامة (Zero-CDN):</strong> كافة المحاكيات تعمل محلياً داخل عازل أمني بحجم (< 200 كيلوبايت) ومحفوظة في المتصفح، لتعمل بكفاءة مطلقة أثناء انقطاع الإنترنت التام.",

    // Studio View
    heroBadgeStudio: "سرب الوكلاء التربوي المستقل",
    heroTitleStudio: "توليد المعامل التفاعلية المستقلة لـ <span>كل طالب</span>.",
    heroSubStudio: "حوّل نصوص المناهج العلمية المعقدة إلى مختبرات برمجية تفاعلية دقيقة، مع تكييف حسي فوري لذوي فرط الحركة وتشتت الانتباه وعسر القراءة.",
    studioFormTitle: "مواصفات الدرس والمدخلات التعليمية",
    studioFormSub: "أدخل بيانات المادة والموضوع لتهيئة سرب الوكلاء المستقلين",
    btnSample: "تحميل نموذج تجريبي",
    lblSubject: "المادة العلمية",
    lblGrade: "الصف الدراسي المستهدف",
    lblTopic: "موضوع التجربة",
    lblText: "فقرة الدرس الأصلية",
    btnRun: "تشغيل سرب الوكلاء",
    guardNotice: "فحص الأمان الحتمي Sandbox Guard مفعّل تلقائياً",
    readyToSend: "جاهز للإرسال",
    charUnit: "حرف",
    pipelineTitle: "مسار المعالجة عبر وكلاء Strands...",

    // Sample Data
    sampleSubject: "الفيزياء",
    sampleTopic: "قانون أوم",
    sampleGrade: "8",
    sampleText: "ينص قانون أوم على أن شدة التيار الكهربائي المار في موصل معدني تتناسب طردياً مع فرق الجهد بين طرفيه عند ثبوت درجة الحرارة. وصيغته الرياضية هي: فرق الجهد = شدة التيار × المقاومة الكهربائية (V = I * R).",

    // Lab Player View
    heroBadgeLab: "محاكي تفاعلي مكتفٍ ذاتياً",
    heroTitleLab: "مشغل المحاكاة التفاعلية <span>المكتفي ذاتياً</span>.",
    heroSubLab: "محاكاة فيزيائية ورياضية تفاعلية آمنة، تعمل محلياً بالكامل بدون أي اتصالات إنترنت خارجية، متوافقة مع الحواسيب المحمولة الضعيفة وشاشات الفصول.",
    emptyLabH: "لا يوجد معمل تفاعلي نشط حالياً",
    emptyLabP: "قم بتشغيل استوديو المناهج لتوليد محاكاة تفاعلية فورية ومحققة أمنياً.",
    btnGotoStudio: "الانتقال إلى استوديو المناهج",
    btnReloadLab: "إعادة ضبط المحاكي",
    btnSaveVault: "حفظ في الخزنة الأوفلاين",
    btnDownloadLab: "تنزيل المختبر المستقل",
    saveToast: "تم الحفظ بنجاح في الخزنة الأوفلاين!",

    // Sensory Suite View
    heroBadgeSensory: "التكيف والتنظيم الحسي العصبي",
    heroTitleSensory: "حزمة التنظيم والتكيف <span>الحسي الشاملة</span>.",
    heroSubSensory: "مخرجات تراعي التنوع العصبي: تجزئة تنفيذية ثلاثية لـ ADHD، نقاط تثبيت بصرية لعسر القراءة، وبروتوكول تجربة منزلية ملموسة.",
    emptySensoryH: "لا توجد بيانات حسية متوفرة حالياً",
    emptySensoryP: "قم بتشغيل سرب الوكلاء في استوديو المناهج لإنتاج بروتوكولات التكيف الحسي.",
    secAdhdTitle: "بروتوكول التركيز الحسي لـ ADHD (تجزئة ثلاثية)",
    secAdhdSub: "تفكيك الحمل المعرفي إلى 3 مراحل تنفيذية حسية متسلسلة",
    secBionicTitle: "التوجيه البصري Bionic Reading (تثبيت العين)",
    secBionicSub: "نقاط ارتكاز بصرية على جذوع الكلمات لمساعدة القراء ذوي عسر القراءة",
    secKitchenTitle: "بروتوكول التجربة المنزلية اليومية",
    secKitchenSub: "ترسيخ المبادئ المجردة باستخدام أدوات منزلية ملموسة متوفرة",

    // Mastery View
    heroBadgeMastery: "تحفيز التفكير السقراطي والرفيق الصوتي",
    heroTitleMastery: "التفكير السقراطي <span>والرفيق الصوتي الذكي</span>.",
    heroSubMastery: "أسئلة تفكير عليا مصممة لنقل المبادئ العلمية وتحدي الحفظ، مقترنة بتسجيلات صوتية اصطناعية عالية الوضوح.",
    emptyMasteryH: "لا يوجد تحدٍ سقراطي متوفر حالياً",
    emptyMasteryP: "قم بتشغيل سرب الوكلاء في استوديو المناهج لإنتاج التحديات السقراطية والحوار الصوتي.",
    secVoiceTitle: "الرفيق الصوتي الذكي والسرد السحابي",
    secVoiceSub: "سرد صوتي تربوي مخصص لتعزيز التعلم متعدد الحواس ودعم اضطراب فرط الحركة ونقص الانتباه (ADHD)",
    btnDownloadAudio: "تحميل المقطع MP3",
    lblTranscriptTitle: "نص السرد المكتوب المتزامن",
    voiceEnginePolly: "سرد سحابي AWS Polly 🎙️",
    voiceEngineNative: "صوت المتصفح المحلي 🔊",
    secSocraticTitle: "تحدي التفكير السقراطي",
    secSocraticSub: "سؤال تفكير عليا يتحدى الحفظ الآلي ويقيس نقل المفاهيم",
    socraticPromptBadge: "تحدي التفكير والبحث",
    lblHypothesis: "الفرضية العلمية للطالب",
    hypothesisPh: "صغ تفسيرك العلمي بناءً على مشاهداتك في المحاكاة...",
    btnCheck: "إرسال الفرضية",
    btnHintReveal: "كشف التلميح التوجيهي",
    btnHintHide: "إخفاء التلميح التوجيهي",
    btnAnswerReveal: "كشف الحل النموذجي",
    btnAnswerHide: "إخفاء الحل النموذجي",
    lblHintBadge: "تلميح تربوي توجيهي",
    lblAnswerBadge: "تفسير نموذجي محقق",

    // Impact Ledger View
    heroBadgeImpact: "سجل التدقيق الحتمي Amazon DynamoDB",
    heroTitleImpact: "سجل الأثر التربوي <span>والاعتماد السحابي</span>.",
    heroSubImpact: "قياسات الأثر التعليمي الموثقة حتمياً: خفض مستوى التعقيد اللغوي، تقليص العبء المعرفي، وسجلات التدقيق الموقعة رقمياً.",
    statGrade: "تبسيط مستوى القراءة",
    statCog: "تقليص العبء الذهني",
    statSize: "حجم الحزمة البرمجية",
    statOffline: "الجاهزية دون إنترنت",
    secCloudStatsTitle: "إحصائيات المنظومة التراكمية عبر السحابة",
    secCloudStatsSub: "معاملات سجل DynamoDB الحية الموثقة عبر منطقة AWS ME-SOUTH-1",
    btnRefresh: "تحديث سجل السحابة",
    lblAuditSessions: "إجمالي الجلسات المسجلة:",
    lblAuditReduction: "متوسط تقليص التعقيد:",
    lblAuditOffline: "المعامل الجاهزة دون إنترنت:",

    // Vault Library View
    heroBadgeVault: "المكتبة المحلية المستقلة",
    heroTitleVault: "معامل STEM التفاعلية <span>المستقلة</span>.",
    heroSubVault: "تشغيل فوري في بيئة معزولة 100% دون الحاجة إلى إنترنت أو خادم. تضم المعامل التأسيسية والمعامل التي تم حفظها من الاستوديو.",
    txtFilterAll: "كافة المعامل",
    txtFilterCore: "المعامل التأسيسية",
    txtFilterSaved: "المحفوظة من السحابة",
    btnLaunchVault: "تشغيل المعمل",
    btnDeleteVault: "حذف",
    vaultTagCore: "تأسيسي",
    vaultTagSaved: "محفوظ محلياً",

    // Runtime Player View
    txtBackVault: "← العودة لمكتبة الخزنة",
    runtimeBadge: "مختبر مستقل أوفلاين",
    btnDownloadRuntime: "تنزيل المختبر (.html)",
    txtRtAdhd: "خطوات ADHD",
    txtRtBionic: "قراءة Bionic",
    txtRtKitchen: "تجربة منزلية",
    txtRtSocratic: "التحدي السقراطي",
    lblRtHintBadge: "تلميح توجيهي",
    lblRtAnswerBadge: "التفسير المعتمد",

    grades: [
      { v: "6", l: "الصف السادس — إعدادي" },
      { v: "7", l: "الصف السابع — إعدادي" },
      { v: "8", l: "الصف الثامن — إعدادي" },
      { v: "9", l: "الصف التاسع — إعدادي" },
      { v: "10", l: "الصف العاشر — ثانوي" },
      { v: "11", l: "الصف الحادي عشر — ثانوي" },
      { v: "12", l: "الصف الثاني عشر — ثانوي" }
    ],

    pipelineSteps: [
      "وكيل 1A: تفكيك مفهوم الدرس وتحديد أهداف الإتقان",
      "وكيل 1B: مطابقة المحرك الرياضي وحدود شجرة AST",
      "وكيل 2A: توليد المحاكاة التفاعلية HTML5/SVG المستقلة",
      "وكيل 2B: فحص الأمان الحتمي Sandbox Guard والتحقق البرمجي",
      "وكيل 3A: إنتاج حزم التكيف الحسي والتحدي السقراطي",
      "سجل AWS: توثيق مقاييس الأثر الحتمية في DynamoDB و S3"
    ]
  }
};

// ============================================================

window.I18N = I18N;
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
      try {
        const errJson = await response.json();
        if (errJson.error) errMsg = errJson.error;
        else if (errJson.detail) errMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      } catch (_) { }
      throw new Error(errMsg);
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
// ============================================================
// LuminaLab Swarm — Offline Standalone Scenario Package Builder (Phase 3)
// 100% Zero-CDN Self-Contained Web Application (< 35 KB)
// Features:
// - Exact Multi-Tab UI: [ Lab | Sensory | Mastery | Impact ]
// - Dynamic In-File Bilingual Toggle (عربي / English)
// - Female Web Speech Companion with Speeds (0.8x, 1.0x, 1.2x) & ADHD Pulse Glow
// - Interactive Collapsible Socratic Challenge (Hint & Model Answer Reveals)
// - Printable Classroom Worksheet Mode (@media print)
// ============================================================

// ============================================================
// Offline Standalone Scenario Package Builder Delegation
// Canonical implementation: src/ui/js/offline/standalone_builder.js
// ============================================================
let _standaloneBuilder = null;
if (typeof require !== "undefined") {
  try {
    _standaloneBuilder = require("./js/offline/standalone_builder.js");
  } catch (e) {
    try {
      _standaloneBuilder = require("./src/ui/js/offline/standalone_builder.js");
    } catch (e2) {}
  }
}

const _existingStandalonePkg = (typeof window !== "undefined" && window.buildStandaloneScenarioPackage) ? window.buildStandaloneScenarioPackage : null;
const _existingExtractScenario = (typeof window !== "undefined" && window.extractBilingualScenario) ? window.extractBilingualScenario : null;

function extractBilingualScenario(scenario, initialIsAr = false) {
  if (_standaloneBuilder && typeof _standaloneBuilder.extractBilingualScenario === "function") {
    return _standaloneBuilder.extractBilingualScenario(scenario, initialIsAr);
  }
  if (_existingExtractScenario && _existingExtractScenario !== extractBilingualScenario) {
    return _existingExtractScenario(scenario, initialIsAr);
  }
  if (typeof window !== "undefined" && window.extractBilingualScenario && window.extractBilingualScenario !== extractBilingualScenario) {
    return window.extractBilingualScenario(scenario, initialIsAr);
  }
  throw new Error("extractBilingualScenario module not available");
}

function buildStandaloneScenarioPackage(scenario, initialIsAr = false) {
  if (_standaloneBuilder && typeof _standaloneBuilder.buildStandaloneScenarioPackage === "function") {
    return _standaloneBuilder.buildStandaloneScenarioPackage(scenario, initialIsAr);
  }
  if (_existingStandalonePkg && _existingStandalonePkg !== buildStandaloneScenarioPackage) {
    return _existingStandalonePkg(scenario, initialIsAr);
  }
  if (typeof window !== "undefined" && window.buildStandaloneScenarioPackage && window.buildStandaloneScenarioPackage !== buildStandaloneScenarioPackage) {
    return window.buildStandaloneScenarioPackage(scenario, initialIsAr);
  }
  throw new Error("buildStandaloneScenarioPackage module not available");
}

if (typeof window !== "undefined") {
  window.extractBilingualScenario = extractBilingualScenario;
  window.buildStandaloneScenarioPackage = buildStandaloneScenarioPackage;
}
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    extractBilingualScenario,
    buildStandaloneScenarioPackage
  };
}
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
window.saveActiveLabToVault = saveActiveLabToVault;
window.downloadVaultScenario = downloadVaultScenario;
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
