from pydantic import BaseModel, Field


class TechDecision(BaseModel):
    category: str = Field(..., description="e.g. database, auth, file_storage, deployment")
    recommended: str = Field(..., description="The recommended technology")
    rationale: str = Field(..., description="1-2 sentences calibrated to skill level")
    alternatives: list[str] = Field(default_factory=list)
    is_required: bool = Field(True)


class StackAnalysisOutput(BaseModel):
    confirmed_stack: list[str] = Field(..., description="What the user explicitly mentioned")
    decisions: list[TechDecision] = Field(default_factory=list)
    complete_stack: list[str] = Field(..., description="All technologies in the final stack")
    folder_structure: str = Field("", description="Recommended top-level structure as ASCII tree")
    skill_assessment: str = Field("", description="One sentence: is this stack appropriate?")