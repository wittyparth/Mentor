from instructor import Instructor, Mode
from openai import AsyncOpenAI
import litellm

from app.core.config import settings
from app.core.encryption import decrypt

from app.models.project import AIProviderConfig


def get_default_ai_client() -> Instructor:
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return Instructor.from_openai(client, mode=Mode.JSON)


def get_ai_client(config: AIProviderConfig) -> Instructor:
    api_key = decrypt(config.api_key_enc)

    if config.provider == "custom" or config.base_url:
        client = AsyncOpenAI(api_key=api_key, base_url=config.base_url)
        return Instructor.from_openai(client, mode=Mode.JSON)

    return Instructor.from_litellm(
        litellm.acompletion,
        mode=Mode.JSON,
        api_key=api_key,
    )


def get_default_model(cheap: bool = True) -> str:
    if cheap:
        return settings.DEFAULT_CHEAP_MODEL
    return settings.DEFAULT_SMART_MODEL


def get_model_for_config(config: AIProviderConfig | None, cheap: bool = True) -> str:
    if config is None:
        return get_default_model(cheap=cheap)
    if config.provider == "openai":
        return config.model_name
    if config.provider == "groq":
        return f"groq/{config.model_name}"
    if config.provider == "openrouter":
        return f"openrouter/{config.model_name}"
    if config.provider == "together":
        return f"together_ai/{config.model_name}"
    return config.model_name