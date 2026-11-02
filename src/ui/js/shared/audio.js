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
