from pydantic import BaseModel, Field


class AIProviderConfigBase(BaseModel):
    provider: str = Field(..., max_length=50, description="openai | groq | openrouter | together | custom")
    model_name: str = Field(..., max_length=100)
    base_url: str | None = Field(default=None, max_length=500)
    api_key: str = Field(..., min_length=1, description="Raw API key - will be encrypted before storage")


class AIProviderConfigCreate(AIProviderConfigBase):
    pass


class AIProviderConfigPublic(BaseModel):
    id: str
    provider: str
    model_name: str
    base_url: str | None = None
    has_key: bool = True
    is_active: bool = True
    created_at: str | None = None


class AIProviderConfigUpdate(BaseModel):
    provider: str | None = None
    model_name: str | None = None
    base_url: str | None = None
    api_key: str | None = None