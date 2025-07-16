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
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.id == usage_id))
        return result.scalar_one_or_none()

    async def get_usages(self, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ApiUsage]:
        """
        List all API usage records with optional pagination.
        """
        result = await db_session.execute(select(ApiUsage).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_user_usages(self, user_id: str, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Get API usage record for a given user.
        """
        result = await db_session.execute(select(ApiUsage).where(ApiUsage.userId == user_id))
        return result.scalar_one_or_none()

    async def increment_chat_usage(self, user_id: str, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Increment chat usage counter by 1 for a given user.
        """
        # Use direct SQL update to avoid ORM type issues
        from sqlalchemy import text
        
        try:
            # First check if the record exists
            result = await db_session.execute(
                text("SELECT id, \"chatUsage\" FROM api_usage WHERE \"userId\" = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            
            if not row:
                return None
            
            usage_id, current_usage = row
            
            # Update the chat usage
            new_usage = (current_usage or 0) + 1
            
            await db_session.execute(
                text("UPDATE api_usage SET \"chatUsage\" = :new_usage, \"updatedAt\" = NOW() WHERE \"userId\" = :user_id"),
                {"new_usage": new_usage, "user_id": user_id}
            )
            
            await db_session.commit()
            
            # Return the updated record
            result = await db_session.execute(
                text("SELECT * FROM api_usage WHERE \"userId\" = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            
            if row:
                # Create an ApiUsage object from the row
                db_usage = ApiUsage(
                    id=row[0],
                    userId=row[1],
                    chatUsage=row[2],
                    invoiceUsage=row[3],
                    resetDate=row[4],
                    createdAt=row[5],
                    updatedAt=row[6]
                )
                return db_usage
            
            return None
            
        except Exception as e:
            await db_session.rollback()
            raise

    async def increment_invoice_usage(self, user_id: str, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Increment invoice usage counter by 1 for a given user.
        """
        print(f"DEBUG: increment_invoice_usage called with user_id: {user_id} (type: {type(user_id)})")
        
        # Use direct SQL update to avoid ORM type issues
        from sqlalchemy import text
        
        try:
            # First check if the record exists
            result = await db_session.execute(
                text("SELECT id, \"invoiceUsage\" FROM api_usage WHERE \"userId\" = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            
            if not row:
                print(f"DEBUG: No usage record found for user_id: {user_id}")
                return None
            
            usage_id, current_usage = row
            print(f"DEBUG: Found usage record - id: {usage_id}, current invoiceUsage: {current_usage}")
            
            # Update the invoice usage
            new_usage = (current_usage or 0) + 1
            print(f"DEBUG: Updating invoiceUsage to: {new_usage}")
            
            await db_session.execute(
                text("UPDATE api_usage SET \"invoiceUsage\" = :new_usage, \"updatedAt\" = NOW() WHERE \"userId\" = :user_id"),
                {"new_usage": new_usage, "user_id": user_id}
            )
            
            await db_session.commit()
            print(f"DEBUG: Successfully committed update")
            
            # Return the updated record
            result = await db_session.execute(
                text("SELECT * FROM api_usage WHERE \"userId\" = :user_id"),
                {"user_id": user_id}
            )
            row = result.fetchone()
            
            if row:
                # Create an ApiUsage object from the row
                db_usage = ApiUsage(
                    id=row[0],
                    userId=row[1],
                    chatUsage=row[2],
                    invoiceUsage=row[3],
                    resetDate=row[4],
                    createdAt=row[5],
                    updatedAt=row[6]
                )
                return db_usage
            
            return None
            
        except Exception as e:
            print(f"DEBUG: Error in increment_invoice_usage: {e}")
            await db_session.rollback()
            raise

    async def update_usage(self, user_id: str, usage: ApiUsageUpdate, db_session: AsyncSession) -> Optional[ApiUsage]:
        """
        Update an API usage record by user ID.
        """
        db_usage = await self.get_user_usages(user_id, db_session)
        if not db_usage:
            return None
        
        update_data = usage.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_usage, field, value)
            
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

    