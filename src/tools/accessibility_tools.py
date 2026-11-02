"""LuminaLab Swarm - Deterministic Accessibility & Sensory Adaptation Tools."""

import re


def _is_arabic(text: str) -> bool:
    """Check if the text contains Arabic characters."""
    return any('\u0600' <= ch <= '\u06FF' for ch in text)


ARABIC_FUNCTIONAL_WORDS = {
    "في", "من", "إلى", "على", "عن", "مع", "بين", "حيث", "هو", "هي", "هما", "هم", "هن",
    "أنا", "نحن", "أنت", "أنتما", "أنتم", "أنتن", "هذا", "هذه", "هذان", "هاتان", "هؤلاء",
    "ذلك", "تلك", "أولئك", "الذي", "التي", "الذين", "اللواتي", "اللاتي",
    "ما", "ماذا", "متى", "أين", "كيف", "كم", "لماذا", "أي", "هل",
    "أن", "إن", "لكن", "لأن", "كي", "حتى", "إذا", "لو", "لولا", "كلما",
    "لا", "لم", "لن", "ليس", "غير", "سوى", "إلا",
    "عند", "قبل", "بعد", "ثم", "أو", "أم", "بل", "فإن", "وإن", "وذلك", "كذلك", "بما", "كما", "وقد", "فقد"
}


def bionic_reading_format(text: str) -> str:
    """
    Converts regular text into Bionic Reading format.
    - For English/Latin text: Bolds the first half of each word (<b>).
    - For Arabic cursive text: Uses whole-word semantic anchoring without severing
      connected letters/ligatures across HTML boundaries.

    Parameters:
        text: Input string (Arabic or English).

    Returns:
        HTML formatted string with <b> tags.
    """
    if not text:
        return ""

    is_ar = _is_arabic(text)
    words = text.split()
    formatted_words = []
    punct_pattern = re.compile(r'([.,!?;:،؟]+)$')

    for word in words:
        match = punct_pattern.search(word)
        if match:
            punct = match.group(1)
            core_word = word[: -len(punct)]
        else:
            punct = ""
            core_word = word

        if is_ar:
            # Arabic cursive orthography: Never sever letters within a single word across HTML tags.
            # Instead, apply semantic whole-word fixation anchors on key content words.
            if len(core_word) <= 2 or core_word.strip() in ARABIC_FUNCTIONAL_WORDS:
                formatted_words.append(word)
            else:
                formatted_words.append(f"<b>{core_word}</b>{punct}")
        else:
            if len(core_word) <= 1:
                formatted_words.append(word)
            else:
                bold_len = max(1, len(core_word) // 2)
                bolded = f"<b>{core_word[:bold_len]}</b>{core_word[bold_len:]}{punct}"
                formatted_words.append(bolded)

    return " ".join(formatted_words)


def adhd_micro_chunk(explanation: str, num_steps: int = 3, language: str | None = None) -> list[str]:
    """
    Splits an explanation into exactly num_steps focused micro-steps with visual color badges.

    Parameters:
        explanation: Full explanatory text.
        num_steps: Number of steps (always 3 for LuminaLab).
        language: Optional language code ('ar' or 'en').

    Returns:
        list of 3 focused strings.
    """
    if not explanation or not explanation.strip():
        explanation = "Explore the interactive simulation to understand this concept."

    is_ar = (language == "ar") or _is_arabic(explanation)
    icons = ["🔵", "🟡", "🟢"]
    prefixes_ar = ["أولاً:", "ثانياً:", "أخيراً:"]
    prefixes_en = ["First:", "Then:", "Finally:"]
    prefixes = prefixes_ar if is_ar else prefixes_en

    # Split by punctuation
    sentences = [s.strip() for s in re.split(r'[.!?،؟\n]+', explanation) if s.strip()]

    if len(sentences) >= num_steps:
        # Distribute sentences evenly across num_steps
        chunk_size = len(sentences) // num_steps
        remainder = len(sentences) % num_steps
        chunks = []
        start = 0
        for i in range(num_steps):
            end = start + chunk_size + (1 if i < remainder else 0)
            chunk_text = ". ".join(sentences[start:end])
            chunks.append(chunk_text)
            start = end
    else:
        # Split words if fewer sentences than num_steps
        words = explanation.split()
        chunk_size = max(1, len(words) // num_steps)
        chunks = []
        for i in range(num_steps):
            if i == num_steps - 1:
                chunk_words = words[i * chunk_size:]
            else:
                chunk_words = words[i * chunk_size : (i + 1) * chunk_size]
            chunks.append(" ".join(chunk_words) if chunk_words else explanation)

    # Ensure exactly 3 steps with badges
    final_steps = []
    for i in range(num_steps):
        text_chunk = chunks[i] if i < len(chunks) and chunks[i] else explanation
        final_steps.append(f"{icons[i]} {prefixes[i]} {text_chunk}")

    return final_steps[:num_steps]


def generate_home_experiment_template(concept: str, language: str = "ar") -> dict:
    """
    Generates a starter template for a free kitchen/home experiment.

    Parameters:
        concept: Target scientific concept.
        language: Language code ('ar' or 'en').

    Returns:
        dict matching the home_experiment structure.
    """
    is_ar = (language == "ar") or _is_arabic(concept)
    if is_ar:
        return {
            "title": f"تجربة بيتية: {concept}",
            "materials": ["أدوات منزلية بسيطة", "ماء وملاعق"],
            "steps": ["الخطوة الأولى: تجهيز الأدوات المنزلية", "الخطوة الثانية: مراقبة النتيجة وتسجيل الملاحظة"],
            "safety_note": "اطلب مساعدة شخص كبير دائماً."
        }
    else:
        return {
            "title": f"Home Experiment: {concept}",
            "materials": ["Household bowl or cup", "Spoon and water"],
            "steps": ["Step 1: Set up the household materials", "Step 2: Observe the interaction and record findings"],
            "safety_note": "Ask an adult for help and supervision."
        }


def generate_voice_script(
    simplified_explanation: str,
    adhd_steps: list[str],
    language: str = "ar",
    grade: int = 8
) -> str:
    """
    Combines simplified explanation and ADHD steps into a sequential audio synthesis script.

    Parameters:
        simplified_explanation: Concise explanation.
        adhd_steps: The 3 ADHD micro-steps.
        language: Language code.
        grade: Student grade level (1-12).

    Returns:
        Structured voice-over script string.
    """
    is_ar = (language == "ar") or _is_arabic(simplified_explanation)
    if grade >= 10:
        intro = "دعنا نتعلم المبدأ العلمي الأساسي لهذه التجربة:" if is_ar else "Let's learn the core scientific principle behind this simulation:"
        outro = "أنت الآن جاهز لاختبار وملاحظة أثر المتغيرات بنفسك داخل المعمل." if is_ar else "You are now ready to test and observe the variables in real time."
    else:
        intro = "يلا نتعلم الكبسولة الذكية دي سوا يا بطل!" if is_ar else "Let's learn your quick science capsule, champion!"
        outro = "عاش يا بطل! إنت كده فهمت السر كله وبأسهل طريقة وزي الفل." if is_ar else "Awesome job, champion! You've unlocked the secret in record time!"

    s0 = adhd_steps[0] if len(adhd_steps) > 0 else ""
    s1 = adhd_steps[1] if len(adhd_steps) > 1 else ""
    s2 = adhd_steps[2] if len(adhd_steps) > 2 else ""

    parts = [
        intro,
        "...",
        simplified_explanation,
        "...",
        s0,
        "...",
        s1,
        "...",
        s2,
        "...",
        outro
    ]
    return "\n".join(parts)
