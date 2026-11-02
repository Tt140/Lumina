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
