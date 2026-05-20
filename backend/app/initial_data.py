import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(session: AsyncSession) -> None:
    result = await session.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_superuser=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)


async def create_initial_data() -> None:
    logger.info("Creating initial data")
    async with AsyncSessionLocal() as session:
        await init_db(session)
    logger.info("Initial data created")