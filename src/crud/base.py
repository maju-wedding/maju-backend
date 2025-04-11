from typing import Any, Generic, TypeVar
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
IDType = TypeVar("IDType", int, str, UUID)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType, IDType]):
    def __init__(self, model: type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model

    async def get(self, db: AsyncSession, id: IDType) -> ModelType | None:
        """
        Get a single record by ID.
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.stream(query)
        return await result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filter_deleted: bool = True
    ) -> list[ModelType]:
        """
        Get multiple records.
        """
        query = select(self.model)

        # Add is_deleted filter if the model has this field and filtering is enabled
        if filter_deleted and hasattr(self.model, "is_deleted"):
            query = query.where(self.model.is_deleted == False)

        query = query.offset(skip).limit(limit)
        result = await db.stream(query)
        return await result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        Update a record.
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: IDType) -> ModelType:
        """
        Physically delete a record.
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def soft_delete(self, db: AsyncSession, *, id: IDType) -> ModelType | None:
        """
        Soft delete a record (set is_deleted=True).
        """
        from utils.utils import utc_now

        obj = await self.get(db, id)
        if obj and hasattr(obj, "is_deleted"):
            obj.is_deleted = True
            if hasattr(obj, "deleted_datetime"):
                obj.deleted_datetime = utc_now()
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj
