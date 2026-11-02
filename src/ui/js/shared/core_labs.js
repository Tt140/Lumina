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
