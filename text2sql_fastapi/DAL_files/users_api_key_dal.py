from models.users_api_key import UsersApiKey
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

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
        Retrieve an API key by its value.
        """
        result = await self.db_session.execute(select(UsersApiKey).where(UsersApiKey.api_key == api_key))
        return result.scalar_one_or_none()

    async def get_user_api_keys(self, user_id):
        """
        List all API keys for a given user.
        """
        result = await self.db_session.execute(select(UsersApiKey).where(UsersApiKey.user_id == user_id))
        return result.scalars().all()

    async def revoke_api_key(self, api_key):
        """
        Revoke (delete) an API key by its value.
        """
        key = await self.get_api_key(api_key)
        if key:
             await self.db_session.delete(key)
             await self.db_session.commit()
        return key 
