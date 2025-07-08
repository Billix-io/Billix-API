from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from models.user_usage import UserUsage
import uuid
from schemas.api_usage_schemas import ApiUsageCreate, ApiUsageUpdate
"""
Data Access Layer for User usage management: create, retrieve, update, delete, and list usage records.
"""

class UserUsageDAL:
    """
    Data Access Layer for User usage management.
    """
    async def get_usage(self, usage_id: str, db_session: AsyncSession) -> Optional[UserUsage]:
        """
        Retrieve a User usage record by its unique ID.
        """
        result = await db_session.execute(select(UserUsage).where(UserUsage.id == usage_id))
        return result.scalar_one_or_none()

    async def get_usages(self, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserUsage]:
        """
        List all User usage records with optional pagination.
        """
        result = await db_session.execute(select(UserUsage).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_user_usage(self, user_id: str, db_session: AsyncSession) -> Optional[UserUsage]:
        """
        Get the User usage record for a given user.
        """
        result = await db_session.execute(select(UserUsage).where(UserUsage.userId == user_id))
        return result.scalar_one_or_none()

    async def update_usage(self, user_id: str,usage: ApiUsageUpdate, db_session: AsyncSession, **kwargs) -> Optional[UserUsage]:
        """
        Update a User usage record by user_id and increment usage counters if provided.
        """
        db_usage = await self.get_user_usage(user_id, db_session)
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

    async def delete_usage(self, usage_id: str, db_session: AsyncSession) -> bool:
        """
        Delete a User usage record by its ID.
        """
        db_usage = await self.get_usage(usage_id, db_session)
        if not db_usage:
            return False
        await db_session.delete(db_usage)
        await db_session.commit()
        return True

    async def create_usage(self, user_id: str, db_session: AsyncSession, chatUsage: int = 0, invoiceUsage: int = 0) -> UserUsage:
        """
        Create a new User usage record for a given user.
        """
        db_usage = UserUsage(
            id=str(uuid.uuid4()),
            userId=user_id,
            chatUsage=chatUsage,
            invoiceUsage=invoiceUsage
        )
        db_session.add(db_usage)
        await db_session.commit()
        await db_session.refresh(db_usage)
        return db_usage
