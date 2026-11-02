import os
from pydantic import BaseModel, Field


try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _parse_bool(val: str | None, default: bool) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "t")


def _resolve_model_id() -> str:
    raw = (
        os.getenv("BEDROCK_MODEL_ID")
        or os.getenv("DEEPSEEK_PRO_MODEL")
        or os.getenv("INCIDENTS_FLASH_MODEL")
        or ("deepseek.v3.2" if ("bedrock-mantle" in os.getenv("OPENAI_BASE_URL", "") or os.getenv("DEEPSEEK_API_KEY")) else "us.amazon.nova-pro-v1:0")
    )
    if raw.startswith("bedrock:"):
        return raw.split("bedrock:", 1)[1]
    return raw


def _resolve_api_key() -> str | None:
    return (
        os.getenv("BEDROCK_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("AWS_BEARER_TOKEN")
        or os.getenv("OPENAI_API_KEY")
    )


def _resolve_base_url() -> str | None:
    explicit = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("DEEPSEEK_BASE_URL")
        or os.getenv("LLM_BASE_URL")
    )
    if explicit:
        return explicit.strip()

    # Smart auto-detection based on key signature for native platform keys
    api_key = _resolve_api_key()
    if api_key and api_key.startswith("sk-"):
        model_id = _resolve_model_id()
        if "deepseek" in model_id.lower():
            return "https://api.deepseek.com"
        # Standard OpenAI keys default to official OpenAI endpoint (no base_url override needed)

    return None



class LuminaConfig(BaseModel):
    LUMINA_MOCK_MODE: bool = Field(
        default_factory=lambda: _parse_bool(os.getenv("LUMINA_MOCK_MODE"), True)
    )
    AWS_REGION: str = Field(
        default_factory=lambda: os.getenv("AWS_REGION", "us-east-1")
    )
    BEDROCK_MODEL_ID: str = Field(
        default_factory=_resolve_model_id
    )
    BEDROCK_API_KEY: str | None = Field(
        default_factory=_resolve_api_key
    )
    LLM_BASE_URL: str | None = Field(
        default_factory=_resolve_base_url
    )
    DYNAMO_TABLE_NAME: str = Field(
        default_factory=lambda: os.getenv("DYNAMO_TABLE_NAME", "luminalab-impact-events")
    )
    S3_BUCKET_NAME: str = Field(
        default_factory=lambda: os.getenv("S3_BUCKET_NAME", "luminalab-vault-057704056750")
    )
    MAX_LAB_SIZE_KB: float = Field(
        default_factory=lambda: float(os.getenv("MAX_LAB_SIZE_KB", "200.0"))
    )
    POLLY_VOICE_AR: str = Field(
        default_factory=lambda: os.getenv("POLLY_VOICE_AR", "Hala")
    )
    POLLY_VOICE_EN: str = Field(
        default_factory=lambda: os.getenv("POLLY_VOICE_EN", "Joanna")
    )


_config_instance: LuminaConfig | None = None


def get_config(reload: bool = False) -> LuminaConfig:
    """Return singleton LuminaConfig instance, reading from environment variables."""
    global _config_instance
    if _config_instance is None or reload:
        _config_instance = LuminaConfig()
    return _config_instance
