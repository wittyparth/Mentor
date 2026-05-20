from fastapi.encoders import jsonable_encoder
from pwdlib.hashers.bcrypt import BcryptHasher
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.repositories import user_repo
from tests.utils.utils import random_email, random_lower_string


async def test_create_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await user_repo.create_user(session=db, user_create=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


async def test_authenticate_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    await user_repo.create_user(session=db, user_create=user_in)
    authenticated_user = await user_repo.authenticate(session=db, email=email, password=password)
    assert authenticated_user
    assert user_repo.User is not None


async def test_not_authenticate_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user = await user_repo.authenticate(session=db, email=email, password=password)
    assert user is None


async def test_check_if_user_is_active(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await user_repo.create_user(session=db, user_create=user_in)
    assert user.is_active is True


async def test_check_if_user_is_active_inactive(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_active=False)
    user = await user_repo.create_user(session=db, user_create=user_in)
    assert user.is_active is False


async def test_check_if_user_is_superuser(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await user_repo.create_user(session=db, user_create=user_in)
    assert user.is_superuser is True


async def test_check_if_user_is_superuser_normal_user(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = await user_repo.create_user(session=db, user_create=user_in)
    assert user.is_superuser is False


async def test_get_user(db: AsyncSession) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await user_repo.create_user(session=db, user_create=user_in)
    user_2 = await db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


async def test_update_user(db: AsyncSession) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = await user_repo.create_user(session=db, user_create=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    if user.id is not None:
        await user_repo.update_user(session=db, db_user=user, user_in=user_in_update)
    user_2 = await db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    verified, _ = verify_password(new_password, user_2.hashed_password)
    assert verified


async def test_authenticate_user_with_bcrypt_upgrades_to_argon2(db: AsyncSession) -> None:
    email = random_email()
    password = random_lower_string()

    bcrypt_hasher = BcryptHasher()
    bcrypt_hash = bcrypt_hasher.hash(password)
    assert bcrypt_hash.startswith("$2")

    user = User(email=email, hashed_password=bcrypt_hash, is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    assert user.hashed_password.startswith("$2")

    authenticated_user = await user_repo.authenticate(session=db, email=email, password=password)
    assert authenticated_user
    assert authenticated_user.email == email

    await db.refresh(authenticated_user)

    assert authenticated_user.hashed_password.startswith("$argon2")

    verified, updated_hash = verify_password(password, authenticated_user.hashed_password)
    assert verified
    assert updated_hash is None