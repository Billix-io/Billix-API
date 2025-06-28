from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from models.api_usage import ApiUsage
from schemas.api_usage_schemas import ApiUsageCreate, ApiUsageUpdate
import uuid

class ApiUsageDAL:
    async def get_usage(self, usage_id: uuid.UUID, db_session: AsyncSession) -> Optional[ApiUsage]:
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.usage_id == usage_id))
        return result.scalar_one_or_none()

    async def get_usages(self, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ApiUsage]:
        result = await db_session.execute(select(ApiUsage).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_user_usages(self, user_id: uuid.UUID, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ApiUsage]:
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.user_id == user_id).offset(skip).limit(limit))
        return result.scalars().all()

    async def update_usage(self, usage_id: uuid.UUID, usage: ApiUsageUpdate, db_session: AsyncSession) -> Optional[ApiUsage]:
        db_usage = await self.get_usage(usage_id, db_session)
        if not db_usage:
            return None
        update_data = usage.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_usage, field, value)
        await db_session.commit()
        await db_session.refresh(db_usage)
        return db_usage

    async def delete_usage(self, usage_id: uuid.UUID, db_session: AsyncSession) -> bool:
        db_usage = await self.get_usage(usage_id, db_session)
        if not db_usage:
            return False
        await db_session.delete(db_usage)
        await db_session.commit()
        return True

    async def create_usage_with_user_id(self, usage_data: ApiUsageCreate,user_id: uuid.UUID, db_session: AsyncSession) -> ApiUsage:
        data = usage_data.model_dump()
        db_usage = ApiUsage(
            **data,
            user_id=user_id
        )
        db_session.add(db_usage)
        await db_session.commit()
        await db_session.refresh(db_usage)
        return db_usage 

    