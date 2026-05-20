from pydantic import BaseModel, Field


class JiraSitePublic(BaseModel):
    cloud_id: str
    name: str
    url: str


class JiraProjectPublic(BaseModel):
    key: str
    name: str


class JiraPushInput(BaseModel):
    cloud_id: str
    project_key: str


class JiraPushResult(BaseModel):
    job_id: str
    message: str = "Jira push job enqueued"