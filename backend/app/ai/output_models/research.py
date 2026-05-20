from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str = Field(..., description="Specific search query for Exa")
    purpose: str = Field("", description="Why this query is important")
    priority: int = Field(1, description="1=critical, 2=important, 3=nice-to-have")


class SearchQueryList(BaseModel):
    queries: list[SearchQuery] = Field(default_factory=list, description="10-14 search queries")


class BeginnerTrap(BaseModel):
    task_area: str
    trap: str = Field(..., description="1 sentence describing the common mistake")
    how_to_avoid: str = Field(..., description="1-2 sentences on avoiding it")


class LearningResource(BaseModel):
    topic: str
    url: str
    description: str


class ResearchBriefOutput(BaseModel):
    final_stack_decisions: list[dict] = Field(default_factory=list)
    architecture_notes: str = ""
    must_have_features: list[str] = Field(default_factory=list)
    nice_to_have_features: list[str] = Field(default_factory=list)
    cut_features: list[str] = Field(default_factory=list)
    beginner_traps: list[BeginnerTrap] = Field(default_factory=list)
    learning_resources: list[LearningResource] = Field(default_factory=list)
    estimated_hours_per_feature: dict = Field(default_factory=dict)