import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt, decrypt
from app.repositories import jira_token_repo
from app.schemas.jira import JiraSitePublic


async def store_jira_tokens(
    *,
    session: AsyncSession,
    user_id: uuid.UUID,
    cloud_id: str,
    site_name: str,
    access_token: str,
    refresh_token: str,
    expires_at=None,
) -> None:
    access_enc = encrypt(access_token)
    refresh_enc = encrypt(refresh_token)

    existing = await jira_token_repo.get_jira_token_by_user_and_cloud(
        session=session, user_id=user_id, cloud_id=cloud_id
    )
    if existing:
        await jira_token_repo.update_jira_token(
            session=session,
            token=existing,
            access_token_enc=access_enc,
            refresh_token_enc=refresh_enc,
            expires_at=expires_at,
        )
    else:
        await jira_token_repo.create_jira_token(
            session=session,
            user_id=user_id,
            cloud_id=cloud_id,
            site_name=site_name,
            access_token_enc=access_enc,
            refresh_token_enc=refresh_enc,
            expires_at=expires_at,
        )


async def get_decrypted_access_token(
    *, session: AsyncSession, user_id: uuid.UUID, cloud_id: str
) -> str | None:
    token = await jira_token_repo.get_jira_token_by_user_and_cloud(
        session=session, user_id=user_id, cloud_id=cloud_id
    )
    if not token:
        return None
    return decrypt(token.access_token_enc)


async def list_jira_sites(
    *, session: AsyncSession, user_id: uuid.UUID
) -> list[JiraSitePublic]:
    tokens = await jira_token_repo.get_jira_tokens_by_user(
        session=session, user_id=user_id
    )
    return [
        JiraSitePublic(cloud_id=t.cloud_id, name=t.site_name or "", url="")
        for t in tokens
    ]