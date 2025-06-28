from models.users_api_key import UsersApiKey
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

class UsersApiKeyDAL:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_api_key(self, user_id, api_key, expires_at=None):
        key = UsersApiKey(user_id=user_id, api_key=api_key, expires_at=expires_at)
        self.db_session.add(key)
        await self.db_session.commit()
        await self.db_session.refresh(key)
        return key

    async def get_api_key(self, api_key):
        result = await self.db_session.execute(select(UsersApiKey).where(UsersApiKey.api_key == api_key))
        return result.scalar_one_or_none()

    async def get_user_api_keys(self, user_id):
        result = await self.db_session.execute(select(UsersApiKey).where(UsersApiKey.user_id == user_id))
        return result.scalars().all()

    async def revoke_api_key(self, api_key):
        key = await self.get_api_key(api_key)
        if key:
            await self.db_session.delete(key)
            await self.db_session.flush()
        return key 
