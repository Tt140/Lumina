"""LuminaLab Swarm - Deterministic Impact Calculator."""

import re
from src.contracts.schemas import ImpactMetrics

TASHKEEL_RE = re.compile(r'[\u064B-\u0652\u0670\u0653-\u065F]')


def count_syllables_en(word: str) -> int:
    """Count syllables for a single English word."""
    clean = re.sub(r'[^a-zA-Z]', '', word).lower()
    if not clean:
        return 1
    groups = re.findall(r'[aeiouy]+', clean)
    count = len(groups)
    if clean.endswith('e') and len(clean) > 2 and count > 1:
        if not clean.endswith(('le', 'ee')) and clean[-2] not in "aeiouy":
            count -= 1
    return max(1, count)


def clean_arabic(word: str) -> str:
    """Remove diacritics and non-alphabetical characters from Arabic word."""
    word = TASHKEEL_RE.sub('', word)
    return re.sub(r'[^\u0621-\u064A]', '', word)


def count_syllables_ar(word: str) -> int:
    """Count syllables for a single Arabic word after removing diacritics."""
    cleaned = clean_arabic(word)
    return max(1, len(cleaned) // 2)


def count_words(text: str) -> int:
    """Count words in a given text (Arabic or English)."""
    if not text or not text.strip():
        return 0
    words = [w for w in text.split() if w.strip()]
    return max(1, len(words))


def count_sentences(text: str) -> int:
    """Count sentences in a text based on punctuation (. ! ? ، ؟ 。)."""
    if not text or not text.strip():
        return 0
    delimiters = re.findall(r'[.!?،؟。]+', text)
    count = len(delimiters)
    last_match = list(re.finditer(r'[.!?،؟。]+', text))
    if last_match:
        trailing = text[last_match[-1].end():].strip()
        if trailing:
            count += 1
    return max(1, count)


def calculate_grade_level(text: str, language: str = "en") -> float:
    """Calculate reading difficulty grade level (1.0-12.0) deterministically."""
    total_words = count_words(text)
    if total_words == 0:
        return 1.0
    total_sentences = count_sentences(text)

    if language == "ar":
        complex_word_count = sum(1 for word in text.split() if len(clean_arabic(word)) > 5)
        grade = 0.5 * (total_words / total_sentences) + 0.3 * (complex_word_count / total_words * 100) + 1.0
    else:
        total_syllables = sum(count_syllables_en(word) for word in text.split())
        grade = 0.39 * (total_words / total_sentences) + 11.8 * (total_syllables / total_words) - 15.59

    return round(max(1.0, min(12.0, grade)), 2)


def calculate_cognitive_load_reduction(baseline_grade: float, simplified_grade: float) -> float:
    """Calculate cognitive load reduction percentage (0.0-100.0)."""
    if baseline_grade <= 0.0:
        return 0.0
    reduction = ((baseline_grade - simplified_grade) / baseline_grade) * 100.0
    return round(max(0.0, min(100.0, reduction)), 2)


def calculate_lab_size_kb(html_content: str) -> float:
    """Calculate HTML source code size in kilobytes (KB)."""
    return round(len(html_content.encode('utf-8')) / 1024.0, 3)


def build_impact_metrics(
    original_text: str,
    simplified_text: str,
    html_content: str,
    language: str,
    generation_time_sec: float
) -> ImpactMetrics:
    """Build complete ImpactMetrics model from raw text inputs."""
    baseline = calculate_grade_level(original_text, language)
    simplified = calculate_grade_level(simplified_text, language)
    reduction = calculate_cognitive_load_reduction(baseline, simplified)
    size_kb = calculate_lab_size_kb(html_content)

    return ImpactMetrics(
        baseline_grade_level=baseline,
        simplified_grade_level=simplified,
        cognitive_load_reduction_pct=reduction,
        lab_size_kb=size_kb,
        generation_time_sec=generation_time_sec
    )
