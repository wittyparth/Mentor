import httpx

from app.core.config import settings


class LinearOAuth:
    LINEAR_AUTH_URL = "https://linear.app/oauth/authorize"
    LINEAR_TOKEN_URL = "https://api.linear.app/oauth/token"

    @staticmethod
    def build_authorization_url(state: str) -> str:
        params = {
            "client_id": settings.LINEAR_CLIENT_ID,
            "redirect_uri": settings.LINEAR_REDIRECT_URI,
            "response_type": "code",
            "scope": "read,write",
            "state": state,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{LinearOAuth.LINEAR_AUTH_URL}?{query}"

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                LinearOAuth.LINEAR_TOKEN_URL,
                data={
                    "client_id": settings.LINEAR_CLIENT_ID,
                    "client_secret": settings.LINEAR_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.LINEAR_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            return resp.json()


class LinearClient:
    BASE_URL = "https://api.linear.app"

    def __init__(self, access_token: str):
        self.access_token = access_token

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method,
                f"{self.BASE_URL}{path}",
                headers=headers,
                **kwargs,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_teams(self) -> list[dict]:
        data = await self._request("GET", "/api/v1/teams")
        return data.get("teams", [])

    async def get_projects(self, team_id: str) -> list[dict]:
        data = await self._request("GET", f"/api/v1/projects?filter[teamId]={team_id}")
        return data.get("nodes", [])

    async def create_project(self, team_id: str, name: str, description: str = "") -> dict:
        return await self._request(
            "POST",
            "/api/v1/projects",
            json={"teamId": team_id, "name": name, "description": description},
        )

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str = "",
        priority: int = 1,
        project_id: str | None = None,
        label_ids: list[str] | None = None,
    ) -> dict:
        payload = {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
        if project_id:
            payload["projectId"] = project_id
        if label_ids:
            payload["labelIds"] = label_ids
        return await self._request("POST", "/api/v1/issues", json=payload)

    async def create_cycle(
        self, team_id: str, name: str, starts_at: str, ends_at: str
    ) -> dict:
        return await self._request(
            "POST",
            "/api/v1/cycles",
            json={
                "teamId": team_id,
                "name": name,
                "startsAt": starts_at,
                "endsAt": ends_at,
            },
        )

    async def get_workflow_states(self, team_id: str) -> list[dict]:
        data = await self._request("GET", f"/api/v1/workflows?filter[teamId]={team_id}")
        return data.get("states", [])