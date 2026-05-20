from pydantic import BaseModel, Field


class ClarificationQuestion(BaseModel):
    question: str = Field(..., description="A clear, friendly question to ask the user")
    why_it_matters: str = Field(..., description="Internal note on why this answer affects the plan")
    is_critical: bool = Field(True, description="Whether this question must be answered")
    suggested_options: list[str] = Field(default_factory=list, description="2-3 short example answers")


class ClarificationResponse(BaseModel):
    questions: list[ClarificationQuestion] = Field(default_factory=list, max_length=4)
    confidence_assessment: str = Field("", description="One sentence: how clear is the input?")