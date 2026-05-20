import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Item
from app.repositories import item_repo
from app.schemas.item import ItemCreate, ItemUpdate


async def create_item(
    *, session: AsyncSession, item_in: ItemCreate, owner_id: uuid.UUID
) -> Item:
    return await item_repo.create_item(session=session, item_in=item_in, owner_id=owner_id)


async def get_items(
    *,
    session: AsyncSession,
    owner_id: uuid.UUID,
    is_superuser: bool,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Item], int]:
    if is_superuser:
        return await item_repo.get_all_items(session=session, skip=skip, limit=limit)
    return await item_repo.get_items_by_owner(
        session=session, owner_id=owner_id, skip=skip, limit=limit
    )


async def get_item_by_id(*, session: AsyncSession, item_id: uuid.UUID) -> Item | None:
    return await item_repo.get_item_by_id(session=session, item_id=item_id)


async def update_item(
    *, session: AsyncSession, db_item: Item, item_in: ItemUpdate
) -> Item:
    update_data = item_in.model_dump(exclude_unset=True)
    return await item_repo.update_item(
        session=session, db_item=db_item, update_data=update_data
    )


async def delete_item(*, session: AsyncSession, item_id: uuid.UUID) -> None:
    await item_repo.delete_item(session=session, item_id=item_id)