from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from models.tool import Tool
from schemas.tool_schemas import ToolCreate, ToolResponse
from database import get_session
 # Assuming OpenAI for LLM, replace with your provider if needed
import os
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine

tool_router = APIRouter()

from agno.agent import Agent
from agno.models.google import Gemini

def generate_sql_template(name: str, description: str) -> str:
    prompt = (
        "You are an expert SQL assistant. Given the following tool name and description, "
        "write a parameterized SQL query template using curly braces for placeholders "
        "(e.g., {column}, {table}, {condition}). Only output the SQL template, nothing else.\n\n"
        f"Name: {name}\nDescription: {description}\nSQL Template:"
    )
    model = Gemini(
        id="gemini-2.0-flash", 
        api_key=os.getenv("GEMINI_API_KEY")  # Or however you load your key
    )
    agent = Agent(model=model)
    response = agent.run(prompt)
    if response and response.content:
        return response.content.strip()
    return ""
    

@tool_router.post("/", response_model=ToolResponse)
async def create_tool(tool: ToolCreate, db: AsyncSession = Depends(get_session)):
    sql_template = tool.sql_template
    if not sql_template:
        # Generate SQL template using LLM if not provided
        sql_template = generate_sql_template(tool.name, tool.description or "")
    db_tool = Tool(
        name=tool.name,
        description=tool.description,
        tool_config=tool.tool_config,
        sql_template=sql_template
    )
    db.add(db_tool)
    await db.commit()
    await db.refresh(db_tool)
    return db_tool

@tool_router.get("/", response_model=List[ToolResponse])
async def list_tools(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Tool))
    return result.scalars().all()

@tool_router.post("/{tool_id}/execute")
async def execute_tool(tool_id: str, params: Dict[str, Any], db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Tool).filter(Tool.tool_id == tool_id))
    tool = result.scalar_one_or_none()
    
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if not tool.sql_template:
        raise HTTPException(status_code=400, detail="Tool has no SQL template")
    
    # Fill in placeholders
    sql = tool.sql_template
    for key, value in params.items():
        sql = sql.replace(f"{{{{{key}}}}}", str(value))
    
    # Use tool_config for DB connection (assume Postgres for now)
    tool_config = tool.tool_config or {}
    db_url = tool_config.get('db_url')
    if not db_url:
        raise HTTPException(status_code=400, detail="Tool config missing db_url")
    
    # Convert sync DB URL to async
    if isinstance(db_url, str) and db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+asyncpg://')
    
    # Connect and execute
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        result = await conn.execute(text(sql))
        rows = [dict(row) for row in result]
    await engine.dispose()
    return {"result": rows, "executed_sql": sql}