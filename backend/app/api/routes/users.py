import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories import user_repo
from app.schemas.common import Message
from app.schemas.user import (
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services import user_service
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
async def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    from sqlalchemy import func, select
    from app.models.user import User as UserModel

    count_stmt = select(func.count()).select_from(UserModel)
    result = await session.execute(count_stmt)
    count = result.scalar_one()

    stmt = (
        select(UserModel)
        .order_by(UserModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    users = list(result.scalars().all())

    users_public = [UserPublic.model_validate(user) for user in users]
    return UsersPublic(data=users_public, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
async def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    user = await user_service.create_user_by_admin(session=session, user_in=user_in)
    return user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    user = await user_service.update_user_me(
        session=session, current_user=current_user, user_in=user_in
    )
    return user


@router.patch("/me/password", response_model=Message)
async def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    await user_service.update_password_me(
        session=session,
        current_user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
async def read_user_me(current_user: CurrentUser) -> Any:
    return current_user


@router.delete("/me", response_model=Message)
async def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    await user_service.delete_user_me(session=session, current_user=current_user)
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
async def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    try:
        user = await user_service.register_user(session=session, user_in=user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    user = await user_repo.get_user_by_id(session=session, user_id=user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
async def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
) -> Any:
    try:
        user = await user_service.update_user_by_admin(
            session=session, user_id=user_id, user_in=user_in
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
async def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    try:
        await user_service.delete_user_by_admin(
            session=session, user_id=user_id, current_user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Message(message="User deleted successfully")