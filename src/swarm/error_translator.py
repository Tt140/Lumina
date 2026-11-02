"""LuminaLab Swarm - Transparent and Secure Error Translation Module.

Translates internal swarm, AWS, API, and Pydantic validation errors into
transparent, human-readable, bilingual diagnostic messages without exposing
sensitive credentials, tokens, or security headers.
"""

import re
import traceback
from typing import Any


def sanitize_error_text(text: str) -> str:
    """
    Strips API keys, bearer tokens, AWS credentials, and authorization headers
    to prevent sensitive credential leakage in client-facing diagnostics.
    """
    if not text or not isinstance(text, str):
        return ""
    # Strip OpenAI / DeepSeek style keys
    scrubbed = re.sub(r'sk-[a-zA-Z0-9_\-]{8,}', '[REDACTED_API_KEY]', text)
    # Strip AWS access keys
    scrubbed = re.sub(r'AKIA[0-9A-Z]{16}', '[REDACTED_AWS_KEY]', scrubbed)
    # Strip Bearer tokens
    scrubbed = re.sub(r'Bearer\s+[a-zA-Z0-9_\.\-]{16,}', 'Bearer [REDACTED_TOKEN]', scrubbed)
    # Strip AWS Security Tokens
    scrubbed = re.sub(r'(?:SecurityToken|SessionToken|X-Amz-Security-Token)[:=]\s*["\']?[a-zA-Z0-9+/=]{20,}["\']?', 'SessionToken=[REDACTED_TOKEN]', scrubbed, flags=re.IGNORECASE)
    # Strip raw Authorization headers
    scrubbed = re.sub(r'(?i)authorization:\s*[^\s,]+', 'Authorization: [REDACTED]', scrubbed)
    return scrubbed.strip()


def translate_swarm_error(exc: Exception, raw_text: str = "") -> dict[str, Any]:
    """
    Classifies an exception into a transparent, actionable diagnostic payload.

    Returns a dict with:
      - error: Brief sanitized message
      - error_code: Categorical enum code
      - title: English title
      - title_ar: Arabic title
      - message: Transparent English explanation of why it happened
      - message_ar: Transparent Arabic explanation of why it happened
      - hint: Actionable English remediation step
      - hint_ar: Actionable Arabic remediation step
    """
    err_str = str(exc)
    err_type = type(exc).__name__
    combined = f"{err_type} {err_str} {raw_text}"
    sanitized_msg = sanitize_error_text(err_str)

    # 1. Token Expired / Authentication Failure
    if any(k in combined for k in [
        "The security token included in the request is expired",
        "ExpiredToken",
        "TokenExpired",
        "InvalidSignatureException",
        "SignatureDoesNotMatch"
    ]):
        return {
            "error": "The AI model security token or session has expired.",
            "error_code": "AUTH_TOKEN_EXPIRED",
            "title": "API Session Token Expired",
            "title_ar": "انتهت صلاحية جلسة مفتاح الذكاء الاصطناعي",
            "message": "The temporary security credentials/session token used to call DeepSeek or AWS Bedrock has expired.",
            "message_ar": "انتهت صلاحية رمز الجلسة المؤقت (Security Token) المستخدم للاتصال بنموذج DeepSeek أو AWS Bedrock.",
            "hint": "Please update or renew DEEPSEEK_API_KEY or AWS session token in your .env file and re-run.",
            "hint_ar": "يرجى تجديد رمز الجلسة أو مفتاح DEEPSEEK_API_KEY في ملف .env ثم إعادة المحاولة."
        }

    # 2. Missing API Key / Credentials
    if any(k in combined for k in [
        "DEEPSEEK_API_KEY is not set",
        "No API key provided",
        "Missing credentials",
        "UnrecognizedClientException",
        "AuthenticationError",
        "401"
    ]):
        return {
            "error": "AI model authentication credentials are missing or invalid.",
            "error_code": "AUTH_KEY_MISSING",
            "title": "API Key Missing or Invalid",
            "title_ar": "مفتاح API غير متوفر أو غير صالح",
            "message": "No valid API key was found in the environment to connect to the model provider.",
            "message_ar": "لم يتم العثور على مفتاح API صالح في بيئة التشغيل للاتصال بمزود الذكاء الاصطناعي.",
            "hint": "Verify that DEEPSEEK_API_KEY is configured in your .env file.",
            "hint_ar": "تأكد من كتابة متغير DEEPSEEK_API_KEY بشكل سليم في ملف .env."
        }

    # 3. Rate Limit / Quota Exceeded
    if any(k in combined for k in [
        "429",
        "RateLimitError",
        "ThrottlingException",
        "TooManyRequests",
        "quota exceeded"
    ]):
        return {
            "error": "Request rate limit reached for the AI provider.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "title": "Rate Limit Exceeded",
            "title_ar": "تم تجاوز معدل الطلبات المسموح",
            "message": "Too many requests were sent to the LLM within a short window, or the quota limit was reached.",
            "message_ar": "تم إرسال عدد كبير من الطلبات لمزود الذكاء الاصطناعي في وقت قصير أو تم الوصول لحد الحصة.",
            "hint": "Wait 10 to 15 seconds before launching another generation request.",
            "hint_ar": "يرجى الانتظار من 10 إلى 15 ثانية قبل إعادة إرسال طلب التوليد."
        }

    # 4. Schema / Pydantic Validation Errors
    if "validation error" in combined.lower() or "validation_error" in combined.lower() or "validationspec" in combined.lower():
        # Extract specific field names if present
        field_match = re.findall(r"([a-zA-Z_]\w*\.\d+|[a-zA-Z_]\w*)\s*\n\s*Input should be", sanitized_msg)
        fields_str = ", ".join(field_match[:3]) if field_match else "simulation parameters"
        return {
            "error": f"Schema validation issue in {fields_str}.",
            "error_code": "SCHEMA_VALIDATION_ERROR",
            "title": "Data Schema Validation Mismatch",
            "title_ar": "خطأ في بنية بيانات المحاكاة (Schema Mismatch)",
            "message": f"The LLM returned simulation components that did not strictly match the expected dictionary structure (Fields: {fields_str}).",
            "message_ar": f"أرجع النموذج بيانات محاكاة غير مطابقة للقالب المتوقع في الحقول ({fields_str}). تم تفعيل التصحيح الذاتي.",
            "hint": "The system auto-heals these structures; simply re-trigger generation or check agent schema sanitizers.",
            "hint_ar": "يقوم النظام بمعالجة هذا النقص آلياً؛ يمكنك إعادة الضغط على توليد وسيعمل بسلاسة."
        }

    # 5. Bedrock ConverseStream / Model Routing Exception
    if "ConverseStream" in combined and "ValidationException" in combined:
        return {
            "error": "Bedrock ConverseStream operation not allowed for this model.",
            "error_code": "MODEL_ROUTING_MISMATCH",
            "title": "Model Routing Incompatibility",
            "title_ar": "عدم توافق في توجيه طلب الموديل",
            "message": "The DeepSeek model cannot be invoked via Bedrock converse-stream directly without the OpenAI Mantle endpoint.",
            "message_ar": "لا يمكن استدعاء موديل DeepSeek عبر converse-stream المباشر دون نقطة وصول Mantle المتوافقة مع OpenAI.",
            "hint": "Ensure DEEPSEEK_API_KEY is supplied so the system routes via the Mantle endpoint.",
            "hint_ar": "تأكد من تعبئة DEEPSEEK_API_KEY لتوجيه الطلب عبر Mantle Endpoint المتوافق."
        }

    # 6. Fallback / Generic Error
    clean_err = sanitized_msg if len(sanitized_msg) < 180 else sanitized_msg[:180] + "..."
    return {
        "error": clean_err,
        "error_code": "INTERNAL_SWARM_ERROR",
        "title": "Pipeline Execution Error",
        "title_ar": "خطأ أثناء تنفيذ مراحل التوليد",
        "message": f"An unexpected error occurred during multi-agent execution: {clean_err}",
        "message_ar": f"حدث خطأ غير متوقع أثناء معالجة الوكلاء: {clean_err}",
        "hint": "Check the terminal logs for detailed stack trace or retry with adjusted text.",
        "hint_ar": "تحقق من سجل الطرفية (Terminal) لمشاهدة التفاصيل بدقة، أو أعد المحاولة."
    }
