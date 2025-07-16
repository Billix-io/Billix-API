from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import Optional, List
from models.api_usage import ApiUsage
from schemas.api_usage_schemas import ApiUsageCreate, ApiUsageUpdate
import uuid
from datetime import datetime

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
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.id == usage_id))
        return result.scalar_one_or_none()

    async def get_usages(self, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ApiUsage]:
        """
        List all API usage records with optional pagination.
        """
        result = await db_session.execute(select(ApiUsage).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_user_usage(self, user_id: str, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Get API usage record for a given user.
        """
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.userId == user_id))
        return result.scalar_one_or_none()

    async def get_or_create_user_usage(self, user_id: str, db_session: AsyncSession) -> ApiUsage:
        """
        Get existing usage record or create a new one for the user.
        """
        usage = await self.get_user_usage(user_id, db_session)
        if not usage:
            # Create new usage record
            usage = ApiUsage(
                userId=user_id,
                chatUsage=0,
                invoiceUsage=0,
                resetDate=datetime.utcnow(),
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )
            db_session.add(usage)
            await db_session.commit()
            await db_session.refresh(usage)
        return usage

    async def increment_chat_usage(self, user_id: str, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Increment chat usage count for a user.
        """
        usage = await self.get_or_create_user_usage(user_id, db_session)
        if usage:
            # Use direct SQL update targeting userId to avoid UUID type issues
            stmt = (
                update(ApiUsage)
                .where(ApiUsage.userId == user_id)
                .values(
                    chatUsage=ApiUsage.chatUsage + 1,
                    updatedAt=datetime.utcnow()
                )
            )
            await db_session.execute(stmt)
            await db_session.commit()
            # Refresh the usage object
            await db_session.refresh(usage)
        return usage

    async def increment_invoice_usage(self, user_id: str, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Increment invoice usage count for a user.
        """
        usage = await self.get_or_create_user_usage(user_id, db_session)
        if usage:
            # Use direct SQL update targeting userId to avoid UUID type issues
            stmt = (
                update(ApiUsage)
                .where(ApiUsage.userId == user_id)
                .values(
                    invoiceUsage=ApiUsage.invoiceUsage + 1,
                    updatedAt=datetime.utcnow()
                )
            )
            await db_session.execute(stmt)
            await db_session.commit()
            # Refresh the usage object
            await db_session.refresh(usage)
        return usage

    async def update_usage(self, user_id: str, usage_update: ApiUsageUpdate, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Update API usage record with specific values.
        """
        usage = await self.get_or_create_user_usage(user_id, db_session)
        if usage:
            update_data = usage_update.dict(exclude_unset=True)
            update_data['updatedAt'] = datetime.utcnow()
            
            stmt = (
                update(ApiUsage)
                .where(ApiUsage.userId == user_id)
                .values(**update_data)
            )
            await db_session.execute(stmt)
            await db_session.commit()
            await db_session.refresh(usage)
        return usage

    async def update_usage_by_id(self, usage_id: uuid.UUID, usage_update: ApiUsageUpdate, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Update API usage record by its ID with specific values.
        """
        usage = await self.get_usage(usage_id, db_session)
        if usage:
            update_data = usage_update.dict(exclude_unset=True)
            update_data['updatedAt'] = datetime.utcnow()
            
            stmt = (
                update(ApiUsage)
                .where(ApiUsage.id == usage_id)
                .values(**update_data)
            )
            await db_session.execute(stmt)
            await db_session.commit()
            await db_session.refresh(usage)
        return usage

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

    