from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.user_database import UserDatabase
from schemas.user_database_schemas import UserDatabaseCreate, UserDatabaseUpdate
from typing import Optional, List
import uuid

"""
Data Access Layer for user database connections: create, retrieve, update, and delete user databases.
"""

class UserDatabaseDAL:
    """
    Data Access Layer for user database connection management.
    """
    def __init__(self, db_session: AsyncSession):
        """
        Initialize with a database session.
        """
        self.db_session = db_session

    async def get_by_id(self, db_id: uuid.UUID) -> Optional[UserDatabase]:
        """
        Retrieve a user database connection by its unique ID.
        """
        result = await self.db_session.execute(select(UserDatabase).where(UserDatabase.db_id == db_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: uuid.UUID) -> List[UserDatabase]:
        """
        List all database connections for a given user.
        """
        result = await self.db_session.execute(select(UserDatabase).where(UserDatabase.user_id == user_id))
        return result.scalars().all()

    async def create(self, db_data: UserDatabaseCreate) -> UserDatabase:
        """
        Create a new user database connection.
        """
        db_obj = UserDatabase(**db_data.dict())
        self.db_session.add(db_obj)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await self.db_session.rollback()
            raise ValueError("Database connection already exists or constraint failed")

    async def update(self, db_id: uuid.UUID, db_update: UserDatabaseUpdate) -> Optional[UserDatabase]:
        """
        Update a user database connection by its ID.
        """
        db_obj = await self.get_by_id(db_id)
        if not db_obj:
            return None
        for field, value in db_update.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_obj)
            return db_obj
        except IntegrityError:
            await self.db_session.rollback()
            raise ValueError("Update failed due to constraint violation")

    async def delete(self, db_id: uuid.UUID) -> bool:
        """
        Delete a user database connection by its ID.
        """
        db_obj = await self.get_by_id(db_id)
        if not db_obj:
            return False
        await self.db_session.delete(db_obj)
        await self.db_session.commit()
        return True 