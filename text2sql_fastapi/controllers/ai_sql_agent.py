from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import json
import re
from agno.agent import Agent
from agno.models.google import Gemini
from tools.sql import SQLTools  # Use your local SQLTools
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.tool import Tool
from database import get_session
from config import settings

load_dotenv()
query_router = APIRouter()

class QueryRequest(BaseModel):
    db_url: str = "mysql+pymysql://sales_user:1234@5.189.160.119:3306/SALES_AI"
    prompt: str = "give me the prompt template of closing interaction mode"

def clean_sql(sql: str) -> str:
    # Remove both ```sql and ``` (optionally surrounded by whitespace)
    sql = re.sub(r"```sql\s*|```", "", sql.strip(), flags=re.IGNORECASE)
    return sql.strip()

@query_router.post("/chat")
async def query_db(request: QueryRequest, db: AsyncSession = Depends(get_session)):
    try:
        # 1. Load all tools
        stmt = select(Tool)
        result = await db.execute(stmt)
        tools = result.scalars().all()
        
        model = Gemini(
            id="gemini-2.0-flash",
            api_key=settings.gemini_api_key
        )
        agent = Agent(model=model)
        
        # 2. Fetch database schema
        sql_tools = SQLTools(db_url=request.db_url)
        table_names = json.loads(sql_tools.list_tables())
        schema = {}
        for table in table_names:
            schema[table] = json.loads(sql_tools.describe_table(table))
        schema_str = "\n".join(
            [f"Table: {table}\nColumns: {schema[table]}" for table in table_names]
        )
        
        # 3. Build prompt for single LLM call (tools + schema + user query)
        tool_list_str = "\n\n".join([
            f"Tool {i+1}:\nName: {t.name}\nDescription: {t.description}\nSQL Template: {t.sql_template}"
            for i, t in enumerate(tools)
        ])
        prompt = (
            "You are an expert SQL assistant. Here are some tools, each with a name, description, and SQL template (with placeholders in curly braces):\n\n"
            f"{tool_list_str}\n\n"
            f"Database schema:\n{schema_str}\n\n"
            f"User Query: {request.prompt}\n\n"
            "Instructions:\n"
            "- Select the best tool for the user query (or 'none' if none match).\n"
            "- If a tool is selected, extract the values for each placeholder from the user query or Database schema, fill the SQL template, and return the filled SQL.\n"
            "- Respond in JSON: {\"used_tool\": <tool name or null>, \"sql_query\": <filled SQL or null>, \"params\": <dict of extracted params or null>}"
        )
        
        response = agent.run(prompt)
        # Try both response_usage and usage attributes for token usage
        token_usage = getattr(response, "response_usage", None) or getattr(response, "usage", None)

        # Fallback: If token_usage is None, estimate using Gemini's count_tokens
        if token_usage is None:
            try:
                gemini_client = model.get_client()
                count_response = gemini_client.models.count_tokens(
                    model=model.id,
                    contents=prompt,
                )
                # count_response should have total_tokens and maybe more
                token_usage = {
                    "total_tokens": getattr(count_response, "total_tokens", None)
                }
            except Exception as e:
                token_usage = {"error": f"Token usage estimation failed: {str(e)}"}

        if response is None or response.content is None:
            raise HTTPException(status_code=500, detail="Failed to get response from LLM")
            
        llm_response = response.content.strip()
        try:
            llm_json = json.loads(llm_response)
        except Exception:
            # If LLM response is not valid JSON, fallback to old logic
            llm_json = {"used_tool": None}
            
        if llm_json.get("used_tool") and llm_json.get("sql_query"):
            sql_query = llm_json["sql_query"]
            if not isinstance(sql_query, str):
                raise HTTPException(status_code=500, detail="Generated SQL query is not a string")
                
            query_result = sql_tools.run_sql_query(sql_query)
            return {
                "used_tool": llm_json["used_tool"],
                "sql_query": sql_query,
                "result": json.loads(query_result) if query_result.startswith("[") else query_result,
                "params": llm_json.get("params"),
                "token_usage": token_usage
            }
        else:
            # Fallback: Use LLM to generate SQL as before
            llm_prompt = (
                f"Database schema:\n{schema_str}\n\n"
                f"User prompt: {request.prompt}\n"
                "Write a SQL query for the above prompt using the schema."
            )
            response = agent.run(llm_prompt)
            token_usage = getattr(response, "response_usage", None) or getattr(response, "usage", None)
            if token_usage is None:
                try:
                    gemini_client = model.get_client()
                    count_response = gemini_client.models.count_tokens(
                        model=model.id,
                        contents=llm_prompt,
                    )
                    token_usage = {
                        "total_tokens": getattr(count_response, "total_tokens", None)
                    }
                except Exception as e:
                    token_usage = {"error": f"Token usage estimation failed: {str(e)}"}
            if response is None or response.content is None:
                raise HTTPException(status_code=500, detail="Failed to get response from LLM")
                
            sql_query = response.content
            if not isinstance(sql_query, str):
                raise HTTPException(status_code=500, detail="Generated SQL query is not a string")
                
            cleaned_query = clean_sql(sql_query)
            if not re.search(r"\bselect\b", cleaned_query, re.IGNORECASE):
                raise HTTPException(status_code=400, detail="Generated content is not a SELECT query.")
                
            query_result = sql_tools.run_sql_query(cleaned_query)
            return {
                "used_tool": None,
                "sql_query": cleaned_query,
                "result": json.loads(query_result) if query_result.startswith("[") else query_result,
                "token_usage": token_usage
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))