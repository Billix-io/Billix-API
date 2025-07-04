"""
Pydantic schemas for SQL tools, including creation, update, and response formats.
"""
from pydantic import BaseModel, UUID4, Field
from typing import Optional, Any
from datetime import datetime

class ToolBase(BaseModel):
    """
    Base schema for SQL tool information, including configuration and template.
    """
    name: str
    description: Optional[str] = None
    tool_config: Optional[Any] = None
    sql_template: Optional[str] = None

class ToolCreate(ToolBase):
    """
    Schema for creating a new SQL tool.
    """
    pass

class ToolUpdate(BaseModel):
    """
    Schema for updating SQL tool fields.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    tool_config: Optional[Any] = None
    sql_template: Optional[str] = None

class ToolInDB(ToolBase):
    """
    Schema for SQL tool data as stored in the database, including ID and timestamps.
    """
    tool_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class ToolResponse(ToolInDB):
    """
    Schema for SQL tool response, inherits from ToolInDB.
    """
    pass    