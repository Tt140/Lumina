"""LuminaLab Swarm - Central Pedagogical & Neuro-Adaptive Calibration.

Calibrates prompts, cognitive load, variable naming, and interactive feedback
across 3 distinct student age & cognitive development tiers:
1. Elementary (Grades 1-6 / Ages 6-11) - Concrete operational, sensory, storytelling.
2. Middle School (Grades 7-9 / Ages 12-14) - Transitional abstract, cause-and-effect, relatable tech/sports.
3. High School (Grades 10-12 / Ages 15-18) - Executive Scientific Capsule ("الزتونة"), mature intuition, exam confidence.
"""

import re
from typing import Any


def parse_student_grade(grade_input: Any) -> int:
    """
    Parses and sanitizes student grade into a normalized integer (1 to 12).
    Handles integers, floats, and strings like 'Grade 11', '10th Grade', 'Grade 5 - Elementary'.
    Defaults to 8 (Middle School baseline) if parsing fails.
    """
    if grade_input is None:
        return 8

    if isinstance(grade_input, (int, float)):
        try:
            val = int(grade_input)
            return max(1, min(12, val))
        except (ValueError, TypeError):
            return 8

    str_val = str(grade_input).strip()
    match = re.search(r"(?:grade\s*)?(\d{1,2})(?:st|nd|rd|th)?", str_val, re.IGNORECASE)
    if match:
        try:
            val = int(match.group(1))
            return max(1, min(12, val))
        except (ValueError, TypeError):
            pass

    str_lower = str_val.lower()
    if any(k in str_lower for k in ["elementary", "primary", "ابتدائي", "child"]):
        return 5
    if any(k in str_lower for k in ["middle", "intermediate", "prep", "إعدادي"]):
        return 8
    if any(k in str_lower for k in ["high", "senior", "secondary", "ثانوي"]):
        return 11

    return 8


def get_pedagogical_tier(grade_input: Any) -> str:
    """
    Categorizes the student into one of three developmental cognitive tiers:
    - 'elementary': Grades 1 to 6
    - 'middle': Grades 7 to 9
    - 'high': Grades 10 to 12
    """
    grade = parse_student_grade(grade_input)
    if grade <= 6:
        return "elementary"
    elif grade <= 9:
        return "middle"
    else:
        return "high"


def get_pedagogical_directive(student_grade: Any, language: str = "ar") -> dict[str, str]:
    """
    Returns age-calibrated and neuro-inclusive pedagogical directives for all swarm agents.
    
    Parameters:
        student_grade: Integer or string representing student grade level.
        language: Language code ('ar' or 'en').
        
    Returns:
        dict containing tailored directives for Concept Deconstruction, Simulation Math,
        ADHD Micro-Chunking, and Socratic Mastery.
    """
    grade = parse_student_grade(student_grade)
    tier = get_pedagogical_tier(grade)
    is_ar = (language == "ar")

    if tier == "elementary":
        tier_label_en = f"Elementary Tier (Grade {grade} - Ages 6-11)"
        tier_label_ar = f"المرحلة الابتدائية (الصف {grade} - الأعمار 6-11 سنة)"

        concept_guidance = (
            "COGNITIVE CALIBRATION (ELEMENTARY TIER):\n"
            "- Cognitive Profile: Concrete operational stage. The student needs tangible, everyday physical metaphors (e.g. water pipes, playground seesaws, bouncing balls, toy cars, colorful blocks).\n"
            "- Tone & Style: Warm, encouraging, wonder-sparking. Short, energetic sentences (maximum 10-12 words per sentence) to prevent visual crowding for Dyslexic and ADHD learners.\n"
            "- Forbidden: NEVER use abstract academic jargon, intimidating formulas, or dry theoretical definitions."
            if not is_ar
            else
            "المعايرة الإدراكية والنفسية (المرحلة الابتدائية - الصفوف 1 إلى 6):\n"
            "- الملف الإدراكي: التفكير العملي الملموس. يحتاج تشبيهات بصرية ملموسة من حياته اليومية (زي خرطوم المياه، الميزان ذو الكفتين، أرجوحة الحديقة، ألعاب البناء).\n"
            "- النبرة والأسلوب: دافئة، مشجعة، تبث الشغف والاستكشاف. جمل قصيرة جداً ومريحة (أقل من 12 كلمة للجملة) لتناسب مرضى عسر القراءة وتشتت الانتباه.\n"
            "- المحظورات: تجنب تماماً المصطلحات الأكاديمية الجافة والرموز المجردة المعقدة."
        )

        math_guidance = (
            "SIMULATION MATH DIRECTIVE (ELEMENTARY TIER):\n"
            "- Variable Bounds: Use clean, friendly integer bounds (e.g. min 1, max 10 or 20) with simple whole-number defaults (e.g. 2, 5, 10).\n"
            "- Variable Naming: Use intuitive descriptive names alongside standard symbols (e.g. 'Pushing Force (F)' or 'Box Weight (W)') so the child immediately grasps what the slider controls.\n"
            "- Simplicity: Avoid intimidating decimals, negative powers, or scientific notation unless physically unavoidable."
            if not is_ar
            else
            "توجيه المحاكي الرياضي (المرحلة الابتدائية):\n"
            "- نطاقات السلايدر: أرقام صحيحة بسيطة ومريحة (مثلاً من 1 إلى 10 أو 1 إلى 20) وقيم افتراضية واضحة (2، 5، 10).\n"
            "- تسمية المتغيرات: أسماء بديهية ملموسة بجانب الرمز (مثلاً: 'قوة السحب (F)' أو 'كتلة الصندوق (m)') ليفهم الطفل فوراً وظيفة السلايدر.\n"
            "- البساطة: تجنب الكسور العشرية المعقدة والأسس السالبة التي تسبب رهبة للطفل."
        )

        adhd_guidance = (
            "ADHD MICRO-CHUNKED DOPAMINE LOOP (ELEMENTARY TIER):\n"
            "- 🔵 Step 1 (Predict & Move): 'First: Slide [Variable Name] and watch how [Visual Element] moves in the drawing!'\n"
            "- 🟡 Step 2 (Spot the Pattern): 'Then: Look closely at the result number—did it grow bigger or smaller when you moved it?'\n"
            "- 🟢 Step 3 (The 'Aha!' Takeaway): 'Finally: Remember that [Core intuitive takeaway in one fun sentence]!'"
            if not is_ar
            else
            "حلقة الدوبامين لـ ADHD (المرحلة الابتدائية):\n"
            "- 🔵 أولاً (حرّك وتوقع): حرّك سلايدر [اسم المتغير] ولاحظ حركة [العنصر البصري] في الرسمة أمامك!\n"
            "- 🟡 ثانياً (اكتشف النمط): قارن حركة الرسمة بالرقم الناتج—هل زادت النتيجة أم صغرت عند تحريك السلايدر؟\n"
            "- 🟢 أخيراً (السر الكبير): تذكر دائماً أن [الخلاصة الممتعة في جملة واحدة سهلة الحفظ]!"
        )

    elif tier == "middle":
        tier_label_en = f"Middle School Tier (Grade {grade} - Ages 12-14)"
        tier_label_ar = f"المرحلة المتوسطة والإعدادية (الصف {grade} - الأعمار 12-14 سنة)"

        concept_guidance = (
            "COGNITIVE CALIBRATION (MIDDLE SCHOOL TIER):\n"
            "- Cognitive Profile: Transitioning to abstract logic. Driven by 'Why does this happen?' and real-world tech, sports, gaming, and smartphone mechanics.\n"
            "- Tone & Style: Smart, engaging peer mentor. Strictly direct Cause-and-Effect ('When X doubles, Y drops by half because...').\n"
            "- Forbidden: ZERO baby-talk or condescending kid phrases. Treat them as emerging young thinkers."
            if not is_ar
            else
            "المعايرة الإدراكية والنفسية (المرحلة المتوسطة/الإعدادية - الصفوف 7 إلى 9):\n"
            "- الملف الإدراكي: التحول للمنطق المجرد. مدفوع بالفضول وسؤال 'لماذا يحدث هذا؟' مع ربط بالتقنية الحديثة والأجهزة والرياضة وسرعة السيارات.\n"
            "- النبرة والأسلوب: مرشد ذكي ومحفز للتفكير. تركيز صارم على السبب والنتيجة المباشرة ('عندما يتضاعف X، يقل Y إلى النصف بسبب...').\n"
            "- المحظورات: تجنب لغة الأطفال أو الاستصغار تماماً. خاطبهم كباحثين شباب."
        )

        math_guidance = (
            "SIMULATION MATH DIRECTIVE (MIDDLE SCHOOL TIER):\n"
            "- Variable Bounds: Use clean standard SI units and relatable real-world ranges with integer or half-integer steps (e.g. 0.5, 1.0, 5.0).\n"
            "- Variable Naming: Standard physical names and SI units (e.g. 'Speed (v)', 'Mass (m)', 'Concentration (C)').\n"
            "- Intuitive Math: Direct and inverse proportionalities clearly expressed."
            if not is_ar
            else
            "توجيه المحاكي الرياضي (المرحلة المتوسطة):\n"
            "- نطاقات السلايدر: وحدات دولية قياسية بنطاقات واقعية وخطوات مريحة (0.5، 1.0، 5.0).\n"
            "- تسمية المتغيرات: الأسماء العلمية الشائعة مع الرموز والوحدات (مثل: 'السرعة (v)', 'الكتلة (m)', 'التركيز (C)').\n"
            "- العلاقات الرياضية: إبراز التناسب الطردي والعكسي بوضوح مباشر."
        )

        adhd_guidance = (
            "ADHD MICRO-CHUNKED DOPAMINE LOOP (MIDDLE SCHOOL TIER):\n"
            "- 🔵 Step 1 (Predict & Move): 'First: Adjust the slider for [Variable Name] and observe the immediate physical reaction in [Visual Component].'\n"
            "- 🟡 Step 2 (Spot the Pattern): 'Then: Track the numerical result—see how changing [Variable] creates a direct proportional shift.'\n"
            "- 🟢 Step 3 (The 'Aha!' Takeaway): 'Finally: The key takeaway is [Crisp cause-and-effect principle].'"
            if not is_ar
            else
            "حلقة الدوبامين لـ ADHD (المرحلة المتوسطة):\n"
            "- 🔵 أولاً (حرّك واختبر): غيّر قيمة سلايدر [اسم المتغير] وراقب التغير الفيزيائي المباشر في [المجسم البصري].\n"
            "- 🟡 ثانياً (اربط السبب بالنتيجة): تابع القيمة الرقمية—لاحظ كيف يسبب تغيير [المتغير] تغيراً طردياً أو عكسياً في النتيجة.\n"
            "- 🟢 أخيراً (الزتونة الذهبية): الخلاصة العلمية هي [مبدأ السبب والنتيجة في جملة مركزة ومباشرة]."
        )

    else:  # high school (10-12)
        tier_label_en = f"Senior High School Tier (Grade {grade} - Ages 15-18)"
        tier_label_ar = f"المرحلة الثانوية والمتقدمة (الصف {grade} - الأعمار 15-18 سنة)"

        concept_guidance = (
            "COGNITIVE CALIBRATION (HIGH SCHOOL / SENIOR TIER):\n"
            "- Cognitive Profile: Mature analytical thinker preparing for exams/university under cognitive and exam pressure. Needs cognitive offloading for ADHD/Dyslexia.\n"
            "- Tone & Style: Executive Scientific Capsule ('الزتونة العلمية المركزة'). Highly respectful, sharp, crystal-clear physical intuition. Demystify the governing mechanism in 2-3 punchy, high-impact sentences that connect formula symbols directly to real-world physical reality (e.g. human physiology, aerospace, clean energy, industrial catalysis).\n"
            "- Forbidden: NEVER use baby talk, childish cartoon analogies, or condescending phrases like 'يا بطل' or 'champ'! NEVER output dry, circular textbook recitation."
            if not is_ar
            else
            "المعايرة الإدراكية والنفسية (المرحلة الثانوية - الصفوف 10 إلى 12):\n"
            "- الملف الإدراكي: مفكر تحليلي ناضج يستعد للامتحانات والجامعة تحت ضغط دراسي وذهني. يحتاج تخفيف العبء الذهني لمرضى ADHD وعسر القراءة.\n"
            "- النبرة والأسلوب: 'الزتونة العلمية المركزة' — احترام كامل لعقلية الطالب، طرح جوهر المبدأ الفيزيائي/الكيميائي/الحيوي بعمق وبساطة ذكية. فكك الآلية الحقيقية للقانون في جملتين أو ثلاث جمل مكثفة تربط رموز المعادلة مباشرة بالواقع العملي (مثل: أمان الشبكات، تنظيم حموضة دم الإنسان، اتزان الهياكل الهندسية).\n"
            "- المحظورات الصارمة: ممنوع منعاً باتاً لغة الأطفال أو عبارات مثل 'يا بطل' أو الرسوم الكرتونية! ممنوع أيضاً السرد الأكاديمي الحلقي الجاف."
        )

        math_guidance = (
            "SIMULATION MATH DIRECTIVE (HIGH SCHOOL / SENIOR TIER):\n"
            "- Variable Bounds: Authentic curriculum-accurate physical/chemical bounds, precise SI units, and standard scientific terminology.\n"
            "- Rigor: Isolate dependent variable cleanly on LHS. Reflect authentic formulas (e.g. dependent = rate * parameter).\n"
            "- Demystification: Ensure slider labels clarify the physical role of each variable in the equation."
            if not is_ar
            else
            "توجيه المحاكي الرياضي (المرحلة الثانوية):\n"
            "- نطاقات السلايدر: حدود دقيقة فيزيائياً وكيميائياً مطابقة للمناهج الدراسية واختبارات القبول، بوحدات SI المعيارية.\n"
            "- الدقة العلمية: عزل المتغير التابع بدقة على يسار المعادلة، وتطبيق القوانين الأصيلة دون تبسيط مخل.\n"
            "- تفكيك الرهبة: صياغة أسماء المتغيرات بطريقة توضح المعنى الفيزيائي لكل رمز في القانون."
        )

        adhd_guidance = (
            "ADHD MICRO-CHUNKED DOPAMINE LOOP (HIGH SCHOOL / SENIOR TIER):\n"
            "- 🔵 Step 1 (Manipulate Mechanism): 'First: Adjust [Variable Symbol / Name] to trigger the physical response in the [Visual Apparatus].'\n"
            "- 🟡 Step 2 (Correlate Rate & Equilibrium): 'Then: Watch the calculated [Result Symbol] and progress meter reflect the exact mathematical relationship.'\n"
            "- 🟢 Step 3 (The Executive Insight): 'Finally: Master the core intuition—[Executive physical mechanism takeaway in one powerful sentence].'"
            if not is_ar
            else
            "حلقة الدوبامين لـ ADHD (المرحلة الثانوية):\n"
            "- 🔵 أولاً (حرّك الآلية الفيزيائية): اضبط سلايدر [اسم/رمز المتغير] وراقب الاستجابة الديناميكية للمنظومة في [المجسم العلمي].\n"
            "- 🟡 ثانياً (حلل معدل التغير): لاحظ كيف تستجيب القيمة المحسوبة [رمز النتيجة] ومؤشر النسبة وفق المعادلة الرياضية بدقة.\n"
            "- 🟢 أخيراً (الزتونة العلمية): رسّخ المبدأ الفيزيائي الحاكم—[الآلية العلمية الحقيقية في جملة تنفيذية حاسمة لا تُنسى]."
        )

    full_directive = f"""=== PEDAGOGICAL DIRECTIVE: {tier_label_en} / {tier_label_ar} ===
{concept_guidance}

{math_guidance}

{adhd_guidance}
============================================================="""

    return {
        "tier": tier,
        "grade": grade,
        "tier_label": tier_label_ar if is_ar else tier_label_en,
        "concept_guidance": concept_guidance,
        "math_guidance": math_guidance,
        "adhd_guidance": adhd_guidance,
        "full_directive": full_directive,
    }
