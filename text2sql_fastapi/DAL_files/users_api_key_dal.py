from models.users_api_key import UsersApiKey
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import selectinload
"""
Data Access Layer for user API key management: create, retrieve, list, and revoke API keys.
"""

class UsersApiKeyDAL:
    """
    Data Access Layer for user API key management.
    """
    def __init__(self, db_session: AsyncSession):
        """
        Initialize with a database session.
        """
        self.db_session = db_session

    async def create_api_key(self, user_id, api_key,name, expires_at=None):
        """
        Create a new API key for a user with optional expiration.
        """
        key = UsersApiKey(user_id=user_id, api_key=api_key, expires_at=expires_at, name= name)
        self.db_session.add(key)
        await self.db_session.commit()
        await self.db_session.refresh(key)
        return key

    async def get_api_key(self, api_key):
        """
        Retrieve an API key by its value, including related api_usages.
        """
        result = await self.db_session.execute(
            select(UsersApiKey).where(UsersApiKey.api_key == api_key)
        )
        # return result.scalar_one_or_none()
        return result.scalars().all()

    async def get_user_api_keys(self, user_id):
        """
        List all API keys for a given user.
        """
        result = await self.db_session.execute(
            select(UsersApiKey).where(UsersApiKey.user_id == user_id)
        )
        return result.scalars().all()
    
    async def update_api_key_name(self, api_key, new_name):
        """
        Update the name of an API key.
        """
        key = await self.get_api_key(api_key)
        if not key:
            return None
        
        setattr(key, 'name', new_name)
        await self.db_session.commit()
        await self.db_session.refresh(key)
        return key

    async def toggle_api_key_status(self, api_key):
        """
        Toggle the active status of an API key using direct SQL UPDATE.
        """
        try:
            # First get the current status
            key = await self.get_api_key(api_key)
            if not key:
                return None
            
            current_status = getattr(key, 'is_active', True)
            new_status = not current_status
            
            # Use direct SQL UPDATE
            result = await self.db_session.execute(
                text("UPDATE users_api_key SET is_active = :is_active WHERE api_key = :api_key"),
                {"is_active": new_status, "api_key": api_key}
            )
            await self.db_session.commit()
            
            # Return the updated key
            return await self.get_api_key(api_key)
        except Exception as e:
            print(f"Error toggling API key status: {e}")
            await self.db_session.rollback()
            return None

    async def revoke_api_key(self, api_key):
        """
        Revoke (delete) an API key by its value.
        """
        key = await self.get_api_key(api_key)
        if key:
             await self.db_session.delete(key)
             await self.db_session.commit()
        return key 
