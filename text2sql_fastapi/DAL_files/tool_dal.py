from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from models.tool import Tool
from schemas.tool_schemas import ToolCreate, ToolUpdate
from typing import Optional, List
import uuid

"""
Data Access Layer for tool management: create, retrieve, update, delete, and list tools.
"""

class ToolDAL:
    """
    Data Access Layer for tool management.
    """
    def __init__(self, db_session: AsyncSession):
        """
        Initialize with a database session.
        """
        self.db_session = db_session

    async def get_by_id(self, tool_id: uuid.UUID) -> Optional[Tool]:
        """
        Retrieve a tool by its unique ID.
        """
        result = await self.db_session.execute(select(Tool).where(Tool.tool_id == tool_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Tool]:
        """
        List all tools in the database.
        """
        result = await self.db_session.execute(select(Tool))
        return result.scalars().all()

    async def create(self, tool_data: ToolCreate) -> Tool:
        """
        Create a new tool in the database.
        """
        tool_obj = Tool(**tool_data.dict())
        self.db_session.add(tool_obj)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(tool_obj)
            return tool_obj
        except IntegrityError:
            await self.db_session.rollback()
            raise ValueError("Tool already exists or constraint failed")

    async def update(self, tool_id: uuid.UUID, tool_update: ToolUpdate) -> Optional[Tool]:
        """
        Update a tool by its ID.
        """
        tool_obj = await self.get_by_id(tool_id)
        if not tool_obj:
            return None
        for field, value in tool_update.dict(exclude_unset=True).items():
            setattr(tool_obj, field, value)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(tool_obj)
            return tool_obj
        except IntegrityError:
            await self.db_session.rollback()
            raise ValueError("Update failed due to constraint violation")

    async def delete(self, tool_id: uuid.UUID) -> bool:
        """
        Delete a tool by its ID.
        """
        tool_obj = await self.get_by_id(tool_id)
        if not tool_obj:
            return False
        await self.db_session.delete(tool_obj)
        await self.db_session.commit()
        return True 