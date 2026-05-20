import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Item
from app.schemas.item import ItemCreate


async def create_item(
    *, session: AsyncSession, item_in: ItemCreate, owner_id: uuid.UUID
) -> Item:
    db_item = Item(
        title=item_in.title,
        description=item_in.description,
        owner_id=owner_id,
    )
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


async def get_item_by_id(
    *, session: AsyncSession, item_id: uuid.UUID
) -> Item | None:
    return await session.get(Item, item_id)


async def get_items_by_owner(
    *, session: AsyncSession, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[Item], int]:
    count_stmt = select(func.count()).select_from(Item).where(Item.owner_id == owner_id)
    count_result = await session.execute(count_stmt)
    count = count_result.scalar_one()

    stmt = (
        select(Item)
        .where(Item.owner_id == owner_id)
        .order_by(Item.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    return items, count


async def get_all_items(
    *, session: AsyncSession, skip: int = 0, limit: int = 100
) -> tuple[list[Item], int]:
    count_stmt = select(func.count()).select_from(Item)
    count_result = await session.execute(count_stmt)
    count = count_result.scalar_one()

    stmt = (
        select(Item).order_by(Item.created_at.desc()).offset(skip).limit(limit)
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())
    return items, count


async def update_item(
    *, session: AsyncSession, db_item: Item, update_data: dict
) -> Item:
    for key, value in update_data.items():
        setattr(db_item, key, value)
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item


async def delete_item(*, session: AsyncSession, item_id: uuid.UUID) -> None:
    item = await session.get(Item, item_id)
    if item:
        await session.delete(item)
        await session.commit()