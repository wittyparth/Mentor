import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import user_repo
from app.schemas.user import UserCreate, UserRegister, UserUpdate, UserUpdateMe
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.utils import generate_new_account_email, send_email


async def register_user(*, session: AsyncSession, user_in: UserRegister) -> User:
    existing = await user_repo.get_user_by_email(session=session, email=user_in.email)
    if existing:
        raise ValueError("A user with this email already exists")
    user_create = UserCreate(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
    )
    return await user_repo.create_user(session=session, user_create=user_create)


async def authenticate_user(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    return await user_repo.authenticate(session=session, email=email, password=password)


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    return await user_repo.get_user_by_email(session=session, email=email)


async def get_user_by_id(*, session: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await user_repo.get_user_by_id(session=session, user_id=user_id)


async def update_user_me(
    *, session: AsyncSession, current_user: User, user_in: UserUpdateMe
) -> User:
    if user_in.email:
        existing = await user_repo.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing and existing.id != current_user.id:
            raise ValueError("A user with this email already exists")
    update_data = user_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


async def update_password_me(
    *, session: AsyncSession, current_user: User, current_password: str, new_password: str
) -> None:
    verified, _ = verify_password(current_password, current_user.hashed_password)
    if not verified:
        raise ValueError("Incorrect password")
    if current_password == new_password:
        raise ValueError("New password cannot be the same as the current one")
    current_user.hashed_password = get_password_hash(new_password)
    session.add(current_user)
    await session.commit()


async def delete_user_me(*, session: AsyncSession, current_user: User) -> None:
    if current_user.is_superuser:
        raise ValueError("Super users are not allowed to delete themselves")
    await session.delete(current_user)
    await session.commit()


async def create_user_by_admin(*, session: AsyncSession, user_in: UserCreate) -> User:
    existing = await user_repo.get_user_by_email(session=session, email=user_in.email)
    if existing:
        raise ValueError("A user with this email already exists")
    user = await user_repo.create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


async def update_user_by_admin(
    *, session: AsyncSession, user_id: uuid.UUID, user_in: UserUpdate
) -> User:
    db_user = await user_repo.get_user_by_id(session=session, user_id=user_id)
    if not db_user:
        raise ValueError("User not found")
    if user_in.email:
        existing = await user_repo.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing and existing.id != user_id:
            raise ValueError("A user with this email already exists")
    return await user_repo.update_user(session=session, db_user=db_user, user_in=user_in)


async def delete_user_by_admin(
    *, session: AsyncSession, user_id: uuid.UUID, current_user: User
) -> None:
    user = await user_repo.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise ValueError("User not found")
    if user.id == current_user.id:
        raise ValueError("Super users are not allowed to delete themselves")
    await user_repo.delete_user(session=session, user_id=user_id)