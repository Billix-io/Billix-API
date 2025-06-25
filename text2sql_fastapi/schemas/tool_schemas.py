from pydantic import BaseModel, UUID4, Field
from typing import Optional, Any
from datetime import datetime

class ToolBase(BaseModel):
    name: str
    description: Optional[str] = None
    tool_config: Optional[Any] = None
    sql_template: Optional[str] = None

class ToolCreate(ToolBase):
    pass

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tool_config: Optional[Any] = None
    sql_template: Optional[str] = None

class ToolInDB(ToolBase):
    tool_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class ToolResponse(ToolInDB):
    pass    