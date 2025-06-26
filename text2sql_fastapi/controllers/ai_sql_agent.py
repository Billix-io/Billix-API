from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
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
from DAL_files.stt_dal import STTDAL
from DAL_files.tts_dal import TTSDAL
from schemas.tts_schemas import TTSRequest, TTSResponse
import base64
from dependencies import get_current_user, payment_required
from schemas.user_schemas import UserBase
from schemas.api_usage_schemas import ApiUsageCreate, ApiUsageUpdate, ApiUsageResponse

load_dotenv()
query_router = APIRouter()
stt_service = STTDAL()
tts_service = TTSDAL()

class QueryRequest(BaseModel):
    db_url: str = "postgresql://user:pass@host:5432/db"
    prompt: str = "What were the top 3 selling products last month?"


def clean_sql(sql: str) -> str:
    # Remove both ```sql and ``` (optionally surrounded by whitespace)
    sql = re.sub(r"```sql\s*|```", "", sql.strip(), flags=re.IGNORECASE)
    return sql.strip()

@query_router.post("/chat")
async def query_db(request: QueryRequest, current_user: UserBase = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
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
        # prompt = (
        #     "You are an expert SQL assistant. Here are some tools, each with a name, description, and SQL template (with placeholders in curly braces):\n\n"
        #     f"{tool_list_str}\n\n"
        #     f"Database schema:\n{schema_str}\n\n"
        #     f"User Query: {request.prompt}\n\n"
        #     "Instructions:\n"
        #     "- Select the best tool for the user query (or 'none' if none match).\n"
        #     "- If a tool is selected, extract the values for each placeholder from the user query or Database schema, fill the SQL template, and return the filled SQL.\n"
        #     "- Respond in JSON: {\"used_tool\": <tool name or null>, \"sql_query\": <filled SQL or null>, \"params\": <dict of extracted params or null>}"
        # )
        prompt = (
    "You are a highly skilled AI SQL assistant designed to translate natural language queries into accurate SQL queries.\n\n"
    "You have access to a set of tools. Each tool includes:\n"
    "- name: The tool's unique name\n"
    "- description: What the tool is designed to do\n"
    "- sql_template: A SQL statement containing placeholders in curly braces that must be filled with values derived from the user query or schema.\n\n"
    f"Available Tools:\n{tool_list_str}\n\n"
    f"Database Schema:\n{schema_str}\n\n"
    f"User Query:\n\"{request.prompt}\"\n\n"
    "Instructions:\n"
    "1. Analyze the user query carefully and match it to the most appropriate tool based on the tool descriptions.\n"
    "   - If no tool is suitable, return 'used_tool': null.\n"
    "2. Identify the correct tables and columns referenced in the query.\n"
    "   - Match them to the database schema, accounting for case sensitivity (table and column names must exactly match schema definitions).\n"
    "   - Ensure you use proper table names and correct capitalization as shown in the schema.\n"
    "3. Extract values for all placeholders in the selected tool's SQL template based on the user query and schema.\n"
    "4. Fill the SQL template with the extracted values.\n\n"
    "Respond ONLY in the following JSON format:\n"
    "{\n"
    '  "used_tool": "<tool_name or null>",\n'
    '  "sql_query": "<completed SQL query or null>",\n'
    '  "params": {<key-value pairs of extracted parameters or null>}\n'
    "}\n\n"
    "Ensure your response is fully parsable JSON, with properly quoted strings and keys."
)
        print("prompt :",prompt)
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
            # Refine the answer using LLM
            refine_prompt = (
                f"User Query: {request.prompt}\n"
                f"SQL Query: {sql_query}\n"
                f"Raw SQL Result: {query_result}\n"
                "\nPlease provide a clear, user-friendly answer to the user's query based on the SQL result above."
            )
            refine_response = agent.run(refine_prompt)
            refined_answer = refine_response.content.strip() if refine_response and refine_response.content else None
            refine_token_usage = getattr(refine_response, "response_usage", None) or getattr(refine_response, "usage", None)
            # Sum token usage if available
            total_token_usage = 0
            if token_usage and isinstance(token_usage, dict) and "total_tokens" in token_usage:
                total_token_usage += token_usage["total_tokens"]
            if refine_token_usage and isinstance(refine_token_usage, dict) and "total_tokens" in refine_token_usage:
                total_token_usage += refine_token_usage["total_tokens"]
            # Log API usage
            usage_create = ApiUsageCreate(
                api_name="llm_query",
                endpoint="/api/v1/query/chat",
                units_used=total_token_usage,
                cost_usd=0,  # You can add cost calculation logic if needed
                api_key_used="N/A",
                status="success"
            )
            await api_usage_service.create_usage_with_user_id(usage_create, current_user.user_id, db)
            return {
                "used_tool": llm_json["used_tool"],
                "sql_query": sql_query,
                "result": json.loads(query_result) if query_result.startswith("[") else query_result,
                "params": llm_json.get("params"),
                "token_usage": token_usage,
                "refine_token_usage": refine_token_usage,
                "total_token_usage": total_token_usage,
                "refined_answer": refined_answer
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
            print("cleaned_query :",cleaned_query)
    
            query_result = sql_tools.run_sql_query(cleaned_query)
            # Refine the answer using LLM
            refine_prompt = (
                f"User Query: {request.prompt}\n"
                f"SQL Query: {cleaned_query}\n"
                f"Raw SQL Result: {query_result}\n"
                "\nPlease provide a clear, user-friendly answer to the user's query based on the SQL result above."
            )
            refine_response = agent.run(refine_prompt)
            refined_answer = refine_response.content.strip() if refine_response and refine_response.content else None
            refine_token_usage = getattr(refine_response, "response_usage", None) or getattr(refine_response, "usage", None)
            # Sum token usage if available
            total_token_usage = 0
            if token_usage and isinstance(token_usage, dict) and "total_tokens" in token_usage:
                total_token_usage += token_usage["total_tokens"]
            if refine_token_usage and isinstance(refine_token_usage, dict) and "total_tokens" in refine_token_usage:
                total_token_usage += refine_token_usage["total_tokens"]
            # Log API usage
            usage_create = ApiUsageCreate(
                api_name="llm_query",
                endpoint="/api/v1/query/chat",
                units_used=total_token_usage,
                cost_usd=0,  # You can add cost calculation logic if needed
                api_key_used="N/A",
                status="success"
            )
            await api_usage_service.create_usage_with_user_id(usage_create, current_user.user_id, db)
            return {
                "used_tool": None,
                "sql_query": cleaned_query,
                "result": json.loads(query_result) if query_result.startswith("[") else query_result,
                "token_usage": token_usage,
                "refine_token_usage": refine_token_usage,
                "total_token_usage": total_token_usage,
                "refined_answer": refined_answer
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@query_router.post("/audio-chat")
async def audio_chat(
    db: AsyncSession = Depends(get_session),
    audio: UploadFile = File(None),
    text: str = None,
):
    """
    Accepts either an audio file or text. If audio is provided, transcribe it, query the DB, and return audio. If text, return text response.
    """
    if audio is not None:
        # 1. Transcribe audio to text
        transcribed_text = await stt_service.speech_to_text(audio)
        # 2. Query the DB using the transcribed text
        request = QueryRequest(prompt=transcribed_text)
        response = await query_db(request, db)
        # 3. Convert the result to audio using TTS
        # Use only the main result text for TTS
        result_text = str(response["result"]) if isinstance(response, dict) and "result" in response else str(response)
        tts_request = TTSRequest(text=result_text)
        audio_bytes = await tts_service.text_to_speech(tts_request)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {"audio_content": audio_b64, "transcription": transcribed_text}
    elif text is not None:
        # 1. Query the DB using the provided text
        request = QueryRequest(prompt=text)
        return await query_db(request, db)
    else:
        raise HTTPException(status_code=400, detail="You must provide either an audio file or text.")