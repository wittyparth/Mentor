import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.config import settings
from app.core.database import AsyncSessionLocal, async_engine
from app.initial_data import create_initial_data
from app.main import app
from app.models.user import Item, User
from app.models.base import Base


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def db() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        await create_initial_data()
        yield session
        await session.execute(delete(Item))
        await session.execute(delete(User))
        await session.commit()


@pytest_asyncio.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="module")
async def superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    from tests.utils.utils import get_superuser_token_headers
    return await get_superuser_token_headers(client)


@pytest_asyncio.fixture(scope="module")
async def normal_user_token_headers(client: AsyncClient, db) -> dict[str, str]:
    from tests.utils.user import authentication_token_from_email
    return await authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )