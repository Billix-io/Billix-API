from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from models.api_usage import ApiUsage
from schemas.api_usage_schemas import ApiUsageCreate, ApiUsageUpdate
import uuid

"""
Data Access Layer for API usage management: create, retrieve, update, delete, and list usage records.
"""

class ApiUsageDAL:
    """
    Data Access Layer for API usage management.
    """
    async def get_usage(self, usage_id: uuid.UUID, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Retrieve an API usage record by its unique ID.
        """
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.usage_id == usage_id))
        return result.scalar_one_or_none()

    async def get_usages(self, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ApiUsage]:
        """
        List all API usage records with optional pagination.
        """
        result = await db_session.execute(select(ApiUsage).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_user_usages(self, user_id: str, db_session: AsyncSession) -> List[ApiUsage]:
        """
        List all API usage records for a given user with optional pagination.
        """
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.userId == user_id))
        result= result.scalar_one_or_none()
        return result

    async def update_usage(self, user_id: str, usage: ApiUsageUpdate, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Update an API usage record by its ID and increment usage counters by 1.
        """
        db_usage = await self.get_user_usages(user_id, db_session)
        print(db_usage.__dict__,"------------")
        if not db_usage:
            return None
        update_data = usage.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_usage, field, value)

        if hasattr(db_usage, 'chatUsage') and db_usage.chatUsage is not None:
            db_usage.chatUsage += 1
        await db_session.commit()
        await db_session.refresh(db_usage)
        return db_usage
    
    async def update_usage(self, user_id: str, usage: ApiUsageUpdate, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Update an API usage record by its ID and increment usage counters by 1.
        """
        db_usage = await self.get_user_usages(user_id, db_session)
        print(db_usage.__dict__,"------------")
        if not db_usage:
            return None
        update_data = usage.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_usage, field, value)

        if hasattr(db_usage, 'invoiceUsage') and db_usage.invoiceUsage is not None:
            db_usage.invoiceUsage += 1
        await db_session.commit()
        await db_session.refresh(db_usage)
        return db_usage

    async def delete_usage(self, usage_id: uuid.UUID, db_session: AsyncSession) -> bool:
        """
        Delete an API usage record by its ID.
        """
        db_usage = await self.get_usage(usage_id, db_session)
        if not db_usage:
            return False
        await db_session.delete(db_usage)
        await db_session.commit()
        return True

    async def create_usage_with_user_id(self, usage_data: ApiUsageCreate, db_session: AsyncSession) -> ApiUsage:
        """
        Create a new API usage record for a given user. chatUsage and invoiceUsage default to 0.
        """
        data = usage_data.model_dump()
        db_usage = ApiUsage(
            **data,
            chatUsage=0,
            invoiceUsage=0
        )
        db_session.add(db_usage)
        await db_session.commit()
        await db_session.refresh(db_usage)
        return db_usage 

    