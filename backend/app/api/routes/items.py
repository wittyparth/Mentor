import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.services import item_service
from app.schemas.item import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from app.schemas.common import Message
from app.models.user import Item

router = APIRouter(prefix="/items", tags=["items"])


async def item_to_public(item: Item) -> ItemPublic:
    return ItemPublic.model_validate(item)


@router.get("/", response_model=ItemsPublic)
async def read_items(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    items, count = await item_service.get_items(
        session=session,
        owner_id=current_user.id,
        is_superuser=current_user.is_superuser,
        skip=skip,
        limit=limit,
    )
    items_public = [await item_to_public(item) for item in items]
    return ItemsPublic(data=items_public, count=count)


@router.get("/{id}", response_model=ItemPublic)
async def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    item = await item_service.get_item_by_id(session=session, item_id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await item_to_public(item)


@router.post("/", response_model=ItemPublic)
async def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    item = await item_service.create_item(
        session=session, item_in=item_in, owner_id=current_user.id
    )
    return await item_to_public(item)


@router.put("/{id}", response_model=ItemPublic)
async def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    item = await item_service.get_item_by_id(session=session, item_id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    updated = await item_service.update_item(
        session=session, db_item=item, item_in=item_in
    )
    return await item_to_public(updated)


@router.delete("/{id}")
async def delete_item(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    item = await item_service.get_item_by_id(session=session, item_id=id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    await item_service.delete_item(session=session, item_id=id)
    return Message(message="Item deleted successfully")