"""LuminaLab Swarm - Shared Resilient JSON Extraction, Repair, and Agent Retry Utilities.

Provides a unified, zero-dependency defense-in-depth layer for all swarm pairs:
1. Extracts ALL assistant text blocks from Strands AgentResult (not just block 0).
2. Preserves the real inner JSONDecodeError instead of masking it with a fallback char-0 error.
3. Repairs common live-LLM JSON glitches (fences, trailing commentary, trailing commas,
   dangling quotes after numeric/boolean literals, unescaped newlines, truncated tails).
4. Runs bounded self-healing retries with targeted error feedback on parse/schema failures,
   while failing fast on authentication errors and backing off on transient rate limits.
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from typing import Any, Callable

from pydantic import BaseModel

logger = logging.getLogger("luminalab.json_utils")

_NON_RETRYABLE_AUTH_MARKERS = (
    "expiredtoken",
    "tokenexpired",
    "the security token included in the request is expired",
    "invalidsignatureexception",
    "signaturedoesnotmatch",
    "unrecognizedclientexception",
    "authenticationerror",
    "accessdenied",
    "bedrock_api_key is not set",
    "no api key provided",
    "missing credentials",
    "401",
    "403",
)

_TRANSIENT_PROVIDER_MARKERS = (
    "429",
    "ratelimit",
    "rate_limit",
    "rate limit",
    "throttl",
    "toomanyrequests",
    "too many requests",
    "timeout",
    "timed out",
    "apiconnectionerror",
    "connection reset",
    "serviceunavailable",
    "502",
    "503",
    "504",
)


def is_non_retryable_provider_error(exc: BaseException) -> bool:
    """Return True for credential/auth/permission errors that should fail fast."""
    combined = f"{type(exc).__name__} {exc}".lower()
    return any(marker in combined for marker in _NON_RETRYABLE_AUTH_MARKERS)


def is_transient_provider_error(exc: BaseException) -> bool:
    """Return True for temporary throttling, timeout, or upstream 5xx network errors."""
    if is_non_retryable_provider_error(exc):
        return False
    combined = f"{type(exc).__name__} {exc}".lower()
    return any(marker in combined for marker in _TRANSIENT_PROVIDER_MARKERS)


def extract_agent_response_text(res: Any) -> str:
    """Extract all assistant text blocks from a Strands AgentResult or raw value."""
    if isinstance(res, str):
        return res

    if hasattr(res, "message") and isinstance(res.message, dict):
        content = res.message.get("content", [])
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict):
                    if "text" in block and isinstance(block["text"], str):
                        parts.append(block["text"])
                elif hasattr(block, "text") and isinstance(getattr(block, "text"), str):
                    parts.append(getattr(block, "text"))
            if parts:
                # If multiple text blocks were produced (e.g. tool narration then JSON),
                # return joined text so downstream JSON extraction can evaluate every candidate.
                return "\n".join(parts)

    if hasattr(res, "text") and isinstance(getattr(res, "text"), str):
        return getattr(res, "text")

    return str(res)


def _strip_markdown_fences(text: str) -> list[str]:
    """Return candidate blocks stripped of Markdown code fences (closed or unclosed)."""
    candidates: list[str] = []

    # Closed ```json ... ``` or ``` ... ``` blocks (prefer last valid JSON block if multiple exist)
    closed_blocks = re.findall(r"```(?:json|JSON)?\s*([\s\S]*?)```", text)
    for blk in reversed(closed_blocks):
        stripped = blk.strip()
        if "{" in stripped:
            candidates.append(stripped)

    # Unclosed opening fence (e.g. truncated stream starting with ```json\n{...)
    if not closed_blocks:
        unclosed = re.sub(r"^\s*```(?:json|JSON)?\s*", "", text.strip())
        unclosed = re.sub(r"\s*```\s*$", "", unclosed).strip()
        if unclosed and unclosed != text.strip():
            candidates.append(unclosed)

    return candidates


def _heal_json_structure(raw: str) -> str:
    """Apply safe syntactic repairs to almost-valid JSON strings."""
    s = raw.strip().lstrip("\ufeff\u200b")

    # Strip opening/closing fences if any remained
    s = re.sub(r"^\s*```(?:json|JSON)?\s*", "", s)
    s = re.sub(r"\s*```\s*$", "", s).strip()

    # Slice from first '{' onward to ignore conversational prefixes
    first_brace = s.find("{")
    if first_brace > 0:
        s = s[first_brace:]

    # Fix Python/JS literals used as JSON values outside keys
    s = re.sub(r":\s*\bTrue\b", ": true", s)
    s = re.sub(r":\s*\bFalse\b", ": false", s)
    s = re.sub(r":\s*\bNone\b", ": null", s)
    s = re.sub(r":\s*-?\b(?:NaN|Infinity)\b", ": null", s)

    # Fix dangling quote after unquoted scalar value before delimiter or next key/brace:
    # e.g. `"default_val":66",` -> `"default_val": 66,`
    # Also handle case where a newline follows the dangling quote before another `"key":`
    s = re.sub(
        r'(:\s*)(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true|false|null)"(\s*(?:[,}\]\n\r]|$))',
        r"\1\2\3",
        s,
    )

    # Remove single-line JS // comments only outside strings, strip trailing commas,
    # insert missing commas between elements, and escape raw newlines inside strings.
    out: list[str] = []
    stack: list[str] = []
    in_string = False
    escaped = False
    i = 0
    n = len(s)

    while i < n:
        ch = s[i]
        if in_string:
            if escaped:
                out.append(ch)
                escaped = False
            elif ch == "\\":
                out.append(ch)
                escaped = True
            elif ch == '"':
                out.append(ch)
                in_string = False
            elif ch == "\n":
                out.append("\\n")
            elif ch == "\r":
                out.append("\\r")
            elif ch == "\t":
                out.append("\\t")
            else:
                out.append(ch)
            i += 1
            continue

        # Outside string
        if ch == "/" and i + 1 < n and s[i + 1] == "/":
            nl = s.find("\n", i)
            i = n if nl == -1 else nl
            continue

        if ch == "/" and i + 1 < n and s[i + 1] == "*":
            end_c = s.find("*/", i + 2)
            i = n if end_c == -1 else end_c + 2
            continue

        if ch == '"':
            # Detect missing comma before a new string key/element after a value token
            j = len(out) - 1
            while j >= 0 and out[j] in (" ", "\t", "\n", "\r"):
                j -= 1
            if j >= 0 and out[j] in ('"', "}", "]", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "e", "l"):
                # Verify trailing alpha is true/false/null before inserting comma
                tail = "".join(out[max(0, j - 4) : j + 1])
                if out[j] in ('"', "}", "]") or out[j].isdigit() or tail.endswith(("true", "false", "null")):
                    out.append(",")
            out.append(ch)
            in_string = True
            i += 1
            continue

        if ch == "{":
            j = len(out) - 1
            while j >= 0 and out[j] in (" ", "\t", "\n", "\r"):
                j -= 1
            if j >= 0 and out[j] in ('"', "}", "]"):
                out.append(",")
            out.append(ch)
            stack.append("}")
            i += 1
            continue

        if ch == "[":
            out.append(ch)
            stack.append("]")
            i += 1
            continue

        if ch in ("}", "]"):
            # Strip trailing comma right before closing delimiter
            j = len(out) - 1
            while j >= 0 and out[j] in (" ", "\t", "\n", "\r"):
                j -= 1
            if j >= 0 and out[j] == ",":
                out[j] = ""
            if stack:
                expected = stack[-1]
                if ch == expected:
                    stack.pop()
                    out.append(ch)
                elif expected == "}" and ch == "]":
                    # Missing '}' before closing ']' (e.g., object in array forgot closing brace)
                    out.append("}")
                    stack.pop()
                    if stack and stack[-1] == "]":
                        stack.pop()
                        out.append("]")
                else:
                    out.append(ch)
            else:
                out.append(ch)
            i += 1
            continue

        out.append(ch)
        i += 1

    if in_string:
        out.append('"')
    # Strip trailing comma before closing truncated stack
    j = len(out) - 1
    while j >= 0 and out[j] in (" ", "\t", "\n", "\r"):
        j -= 1
    if j >= 0 and out[j] == ",":
        out[j] = ""
    while stack:
        out.append(stack.pop())

    return "".join(out)


def _decode_best_dict(candidate: str) -> tuple[dict[str, Any] | None, json.JSONDecodeError | None]:
    """Scan all `{` positions using JSONDecoder.raw_decode; pick largest dict or return deepest error."""
    decoder = json.JSONDecoder()
    best_obj: dict[str, Any] | None = None
    best_span = -1
    deepest_err: json.JSONDecodeError | None = None

    idx = candidate.find("{")
    while idx != -1:
        try:
            obj, end_idx = decoder.raw_decode(candidate, idx)
            if isinstance(obj, dict) and (end_idx - idx) > best_span:
                best_obj = obj
                best_span = end_idx - idx
        except json.JSONDecodeError as exc:
            if deepest_err is None or exc.pos >= deepest_err.pos:
                deepest_err = exc
        idx = candidate.find("{", idx + 1)

    return best_obj, deepest_err


def _normalize_smart_quotes_if_needed(text: str) -> str:
    """Replace curly double quotes around JSON structure only if standard parsing failed."""
    return text.replace("\u201c", '"').replace("\u201d", '"')


def extract_json_dict(text: str) -> dict[str, Any]:
    """Parse a JSON dictionary from raw LLM output without masking real inner errors."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Empty response text received from agent.")

    clean_text = text.strip()
    candidates: list[str] = []
    candidates.extend(_strip_markdown_fences(clean_text))

    start = clean_text.find("{")
    end = clean_text.rfind("}")
    if start != -1 and end > start:
        slice_obj = clean_text[start : end + 1]
        if slice_obj not in candidates:
            candidates.append(slice_obj)
    if start != -1 and clean_text[start:] not in candidates:
        candidates.append(clean_text[start:])
    if clean_text not in candidates:
        candidates.append(clean_text)

    primary_err: json.JSONDecodeError | None = None

    # Pass 1: strict raw_decode / json.loads across all isolated candidates
    for cand in candidates:
        try:
            direct = json.loads(cand)
            if isinstance(direct, dict):
                return direct
        except json.JSONDecodeError as exc:
            if primary_err is None:
                primary_err = exc

        obj, scan_err = _decode_best_dict(cand)
        if obj is not None:
            return obj
        if scan_err is not None and (primary_err is None or scan_err.pos > primary_err.pos):
            primary_err = scan_err

    # Pass 2: deterministic syntax healing on fenced/brace-sliced candidates (never raw ``` first)
    for cand in candidates:
        for variant in (cand, _normalize_smart_quotes_if_needed(cand)):
            repaired = _heal_json_structure(variant)
            try:
                parsed = json.loads(repaired)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
            obj, _ = _decode_best_dict(repaired)
            if obj is not None:
                return obj

    if primary_err is not None:
        snippet_start = max(0, primary_err.pos - 60)
        snippet_end = min(len(candidates[0]), primary_err.pos + 60)
        context_slice = candidates[0][snippet_start:snippet_end].replace("\n", "\\n")
        raise ValueError(
            f"Malformed JSON at line {primary_err.lineno}, column {primary_err.colno}: "
            f"{primary_err.msg} (near: {context_slice!r})"
        ) from primary_err

    raise ValueError(f"No JSON object found in agent output (starts with: {clean_text[:80]!r})")


def _build_repair_prompt(
    original_prompt: str,
    raw_output: str,
    error: Exception,
    required_hint: str = "",
) -> str:
    """Build a crisp self-healing prompt carrying exact error location without bloating context."""
    excerpt = (raw_output or "").strip()
    if len(excerpt) > 1000:
        excerpt = excerpt[:450] + "\n...[truncated]...\n" + excerpt[-450:]

    parts = [
        "Your previous response could not be parsed or validated as a valid JSON object.",
        f"Exact error: {error}",
    ]
    if required_hint:
        parts.append(f"Schema requirement: {required_hint}")
    if excerpt:
        parts.append(f"Broken output excerpt:\n{excerpt}")
    parts.append(
        "Fix the syntax/schema error and return ONLY ONE strictly valid JSON object "
        "(no markdown code fences, no duplicate array objects, no trailing quotes after numbers, no commentary)."
    )
    parts.append(f"Original request context:\n{original_prompt[:1500]}")
    return "\n\n".join(parts)


def invoke_agent_for_json(
    agent: Any,
    prompt: str,
    *,
    max_json_attempts: int = 3,
    max_transient_attempts: int = 2,
    normalizer: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    schema_cls: type[BaseModel] | None = None,
    required_hint: str = "",
    agent_label: str = "Agent",
) -> dict[str, Any]:
    """Invoke an agent with bounded transient-error backoff and self-healing JSON/schema retries."""
    current_prompt = prompt
    last_error: Exception | None = None

    for json_attempt in range(1, max(1, max_json_attempts) + 1):
        res = None
        for net_attempt in range(1, max(1, max_transient_attempts) + 1):
            try:
                res = agent(current_prompt)
                break
            except Exception as exc:
                if is_non_retryable_provider_error(exc):
                    raise
                if is_transient_provider_error(exc) and net_attempt < max_transient_attempts:
                    delay = min(4.0, (0.75 * (2 ** (net_attempt - 1))) + random.uniform(0.05, 0.35))
                    logger.warning(
                        f"[{agent_label}] Transient provider error ({exc}); retrying in {delay:.2f}s "
                        f"(attempt {net_attempt}/{max_transient_attempts})"
                    )
                    time.sleep(delay)
                    continue
                raise

        raw_text = extract_agent_response_text(res)
        try:
            parsed = extract_json_dict(raw_text)
            if normalizer is not None:
                parsed = normalizer(parsed)
            if schema_cls is not None:
                schema_cls.model_validate(parsed)
            return parsed
        except Exception as exc:
            last_error = exc
            if json_attempt >= max_json_attempts:
                break
            logger.warning(
                f"[{agent_label}] Self-healing retry {json_attempt}/{max_json_attempts} "
                f"after JSON/schema failure: {exc}"
            )
            # Reset conversation messages between repair attempts so malformed history does not accumulate
            if hasattr(agent, "messages") and isinstance(agent.messages, list):
                agent.messages.clear()
            current_prompt = _build_repair_prompt(prompt, raw_text, exc, required_hint=required_hint)

    assert last_error is not None
    raise ValueError(f"{agent_label} failed JSON/schema parsing after {max_json_attempts} attempt(s): {last_error}") from last_error
