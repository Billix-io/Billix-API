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
from dependencies import api_key_auth
from schemas.api_usage_schemas import ApiUsageCreate, ApiUsageUpdate, ApiUsageResponse
from models.user_subscription import UserSubscription
from models.api_usage import ApiUsage
from DAL_files.user_subscription_dal import UserSubscriptionDAL
from DAL_files.api_usage_dal import ApiUsageDAL

load_dotenv()
query_router = APIRouter()
stt_service = STTDAL()
tts_service = TTSDAL()
api_usage_service = ApiUsageDAL()


class QueryRequest(BaseModel):
    db_url: str = "postgresql://user:pass@host:5432/db"
    prompt: str = "What were the top 3 selling products last month?"


def clean_sql(sql: str) -> str:
    # Remove both ```sql and ``` (optionally surrounded by whitespace)
    sql = re.sub(r"```sql\s*|```", "", sql.strip(), flags=re.IGNORECASE)
    
    # Remove any markdown formatting
    sql = re.sub(r"\*\*.*?\*\*", "", sql)  # Remove bold text
    sql = re.sub(r"\*.*?\*", "", sql)      # Remove italic text
    
    # Remove any explanatory text before or after the SQL
    # Look for SQL keywords to find the actual query
    sql_keywords = r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\b"
    match = re.search(sql_keywords, sql, re.IGNORECASE)
    if match:
        # Start from the first SQL keyword
        sql = sql[match.start():]
    
    # Remove any trailing text after semicolon or closing parenthesis
    sql = re.sub(r";.*$", ";", sql, flags=re.DOTALL)
    
    # Clean up whitespace
    sql = re.sub(r'\s+', ' ', sql.strip())
    
    return sql.strip()

@query_router.post("/chat")
async def query_db(request: QueryRequest, db: AsyncSession = Depends(get_session), user_id: str = Depends(api_key_auth)):
    model = Gemini(
        id="gemini-2.0-flash",
        api_key=settings.gemini_api_key
    )
    agent = Agent(model=model)
    
    # If db_url is not provided, just chat
    if not request.db_url:
        response = agent.run(f"User: {request.prompt}\nAI:")
        return {"response": response.content.strip() if response and response.content else "Sorry, I couldn't generate a response."}
    
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
    "2.MOST IMPORTANT - **Identify the correct tables and columns referenced in the query.**\n"
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
            await api_usage_service.create_usage_with_user_id(usage_create, user_id, db)
            # Deduct tokens from user_subscription
            subscription_dal = UserSubscriptionDAL(db)
            subscription = await subscription_dal.get_by_user_id(user_id)
            if subscription:
                new_tokens = int(subscription.tokens_remaining) - int(total_token_usage)
                subscription.tokens_remaining = new_tokens
                await db.commit()
                await db.refresh(subscription)
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
            refined_answer = refine_response.content.strip() if refine_response else None
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
            await api_usage_service.create_usage_with_user_id(usage_create, user_id, db)
            # Deduct tokens from user_subscription
            subscription_dal = UserSubscriptionDAL(db)
            subscription = await subscription_dal.get_by_user_id(user_id)
            if subscription:
                new_tokens = int(subscription.tokens_remaining) - int(total_token_usage)
                subscription.tokens_remaining = new_tokens
                await db.commit()
                await db.refresh(subscription)
            return {
                "used_tool": None,
                "sql_query": cleaned_query,
                "result": json.loads(query_result) if query_result.startswith("[") else query_result,
                "token_usage": token_usage,
                "refine_token_usage": refine_token_usage,
                "total_token_usage": total_token_usage,
                "refined_answer": refined_answer
            }
    except HTTPException as e:
        if e.status_code == 400 and str(e.detail).startswith("Generated content is not a SELECT query"):
            # Instead of falling back to conversational response, try to generate a proper SQL query
            try:
                # Try one more time with a more explicit prompt
                retry_prompt = (
                    f"Database schema:\n{schema_str}\n\n"
                    f"User question: {request.prompt}\n\n"
                    "Generate a SELECT SQL query to answer this question. The query must:\n"
                    "1. Start with SELECT\n"
                    "2. Use tables from the schema above\n"
                    "3. Be a valid SQL statement\n\n"
                    "Write ONLY the SQL query:"
                )
                
                retry_response = agent.run(retry_prompt)
                retry_sql = retry_response.content.strip()
                cleaned_query = clean_sql(retry_sql)
                
                if re.search(r"\bselect\b", cleaned_query, re.IGNORECASE):
                    query_result = sql_tools.run_sql_query(cleaned_query)
                    refine_prompt = (
                        f"User Query: {request.prompt}\n"
                        f"SQL Query: {cleaned_query}\n"
                        f"Raw SQL Result: {query_result}\n"
                        "Provide a clear answer."
                    )
                    refine_response = agent.run(refine_prompt)
                    refined_answer = refine_response.content.strip() if refine_response else None
                    
                    return {
                        "used_tool": None,
                        "sql_query": cleaned_query,
                        "result": json.loads(query_result) if query_result.startswith("[") else query_result,
                        "refined_answer": refined_answer
                    }
                else:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Unable to generate a SELECT query for your request. Please rephrase your question to be more specific about what data you want to retrieve."
                    )
            except Exception as retry_error:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Unable to generate a SELECT query for your request. Please rephrase your question to be more specific about what data you want to retrieve."
                )
        else:
            raise
    except Exception as e:
        # As a last resort, try to generate SQL one more time
        try:
            retry_prompt = (
                f"Database schema:\n{schema_str}\n\n"
                f"User question: {request.prompt}\n\n"
                "Generate a SELECT SQL query to answer this question. The query must:\n"
                "1. Start with SELECT\n"
                "2. Use tables from the schema above\n"
                "3. Be a valid SQL statement\n\n"
                "Write ONLY the SQL query:"
            )
            
            retry_response = agent.run(retry_prompt)
            retry_sql = retry_response.content.strip()
            cleaned_query = clean_sql(retry_sql)
            
            if re.search(r"\bselect\b", cleaned_query, re.IGNORECASE):
                query_result = sql_tools.run_sql_query(cleaned_query)
                refine_prompt = (
                    f"User Query: {request.prompt}\n"
                    f"SQL Query: {cleaned_query}\n"
                    f"Raw SQL Result: {query_result}\n"
                    "Provide a clear answer."
                )
                refine_response = agent.run(refine_prompt)
                refined_answer = refine_response.content.strip() if refine_response else None
                
                return {
                    "used_tool": None,
                    "sql_query": cleaned_query,
                    "result": json.loads(query_result) if query_result.startswith("[") else query_result,
                    "refined_answer": refined_answer
                }
            else:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Error processing your request: {str(e)}"
                )
        except Exception as final_error:
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing your request: {str(e)}"
            )



async def handle_query_logic(request, user_id, db, tools, agent: Agent, api_usage_service: ApiUsageDAL):
    # Get DB schema
    sql_tools = SQLTools(db_url=request.db_url)
    table_names = json.loads(sql_tools.list_tables())
    schema = {
        table: json.loads(sql_tools.describe_table(table)) for table in table_names
    }
    schema_str = "\n".join([f"Table: {table}\nColumns: {schema[table]}" for table in table_names])

    tool_list_str = "\n\n".join([
        f"Tool {i+1}:\nName: {t.name}\nDescription: {t.description}\nSQL Template: {t.sql_template}"
        for i, t in enumerate(tools)
    ])

    # Compose prompt
    prompt = (
        "You are a highly skilled AI SQL assistant designed to translate natural language queries into accurate SQL queries.\n\n"
        f"Available Tools:\n{tool_list_str}\n\n"
        f"Database Schema:\n{schema_str}\n\n"
        f"User Query:\n\"{request.prompt}\"\n\n"
        "Instructions:\n"
        "- Match tools\n"
        "- Extract values\n"
        "- Fill SQL template\n"
        "- Respond ONLY in JSON:\n"
        "{ \"used_tool\": <tool_name or null>, \"sql_query\": <sql or null>, \"params\": {<extracted params or null>} }"
    )

    response = agent.run(prompt)
    token_usage = getattr(response, "response_usage", None) or getattr(response, "usage", None)

    if token_usage is None:
        try:
            gemini_client = agent.model.get_client()
            token_usage = {
                "total_tokens": gemini_client.models.count_tokens(model=agent.model.id, contents=prompt).total_tokens
            }
        except Exception as e:
            token_usage = {"error": str(e)}

    if response is None or response.content is None:
        raise HTTPException(status_code=500, detail="LLM response empty")

    try:
        llm_json = json.loads(response.content.strip())
    except Exception:
        llm_json = {"used_tool": None}

    total_token_usage = token_usage.get("total_tokens", 0)

    if llm_json.get("used_tool") and llm_json.get("sql_query"):
        sql_query = llm_json["sql_query"]
        if not isinstance(sql_query, str):
            raise HTTPException(status_code=500, detail="Invalid SQL string from LLM")

        query_result = sql_tools.run_sql_query(sql_query)

        refine_prompt = (
            f"User Query: {request.prompt}\n"
            f"SQL Query: {sql_query}\n"
            f"Raw SQL Result: {query_result}\n"
            "Please provide a clear, user-friendly answer."
        )

        refine_response = agent.run(refine_prompt)
        refined_answer = refine_response.content.strip() if refine_response else None
        refine_token_usage = getattr(refine_response, "response_usage", None) or getattr(refine_response, "usage", None)

        if refine_token_usage and "total_tokens" in refine_token_usage:
            total_token_usage += refine_token_usage["total_tokens"]

        # log API usage
        usage_create = ApiUsageCreate(
            api_name="llm_query",
            endpoint="/api/v1/query/chat",
            units_used=total_token_usage,
            cost_usd=0,
            api_key_used="N/A",
            status="success"
        )
        await api_usage_service.create_usage_with_user_id(usage_create, user_id, db)

        subscription_dal = UserSubscriptionDAL(db)
        subscription = await subscription_dal.get_by_user_id(user_id)
        if subscription:
            subscription.tokens_remaining = int(subscription.tokens_remaining) - int(total_token_usage)
            await db.commit()
            await db.refresh(subscription)

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

    # fallback if no tool
    fallback_prompt = (
        f"Database schema:\n{schema_str}\n\n"
        f"User prompt: {request.prompt}\n\n"
        "You are a SQL expert. Generate ONLY a SELECT query that answers the user's question.\n"
        "Requirements:\n"
        "- Must be a SELECT query only\n"
        "- Must use the provided database schema\n"
        "- Must be valid SQL syntax\n"
        "- Return ONLY the SQL query, no explanations or markdown formatting\n"
        "- If you cannot create a SELECT query, respond with 'ERROR: Cannot generate SELECT query'\n\n"
        "SQL Query:"
    )
    response = agent.run(fallback_prompt)
    fallback_sql = response.content.strip()
    cleaned_query = clean_sql(fallback_sql)

    # Check if the response indicates an error or doesn't contain SELECT
    if (not cleaned_query or 
        cleaned_query.lower().startswith("error:") or 
        not re.search(r"\bselect\b", cleaned_query, re.IGNORECASE)):
        
        # Try one more time with a more explicit prompt
        retry_prompt = (
            f"Database schema:\n{schema_str}\n\n"
            f"User question: {request.prompt}\n\n"
            "Generate a SELECT SQL query to answer this question. The query must:\n"
            "1. Start with SELECT\n"
            "2. Use tables from the schema above\n"
            "3. Be a valid SQL statement\n\n"
            "Write ONLY the SQL query:"
        )
        
        retry_response = agent.run(retry_prompt)
        retry_sql = retry_response.content.strip()
        cleaned_query = clean_sql(retry_sql)
        
        # If still no SELECT query, provide a helpful error
        if not re.search(r"\bselect\b", cleaned_query, re.IGNORECASE):
            raise HTTPException(
                status_code=400, 
                detail=f"Unable to generate a SELECT query for your request. Please rephrase your question to be more specific about what data you want to retrieve. Original response: {cleaned_query[:200]}..."
            )

    query_result = sql_tools.run_sql_query(cleaned_query)

    refine_prompt = (
        f"User Query: {request.prompt}\n"
        f"SQL Query: {cleaned_query}\n"
        f"Raw SQL Result: {query_result}\n"
        "Provide a clear answer."
    )
    refine_response = agent.run(refine_prompt)
    refined_answer = refine_response.content.strip() if refine_response else None
    refine_token_usage = getattr(refine_response, "response_usage", None) or getattr(refine_response, "usage", None)
    if refine_token_usage and "total_tokens" in refine_token_usage:
        total_token_usage += refine_token_usage["total_tokens"]

    usage_create = ApiUsageCreate(
        api_name="llm_query",
        endpoint="/api/v1/query/chat",
        units_used=total_token_usage,
        cost_usd=0,
        api_key_used="N/A",
        status="success"
    )
    await api_usage_service.create_usage_with_user_id(usage_create, user_id, db)

    subscription_dal = UserSubscriptionDAL(db)
    subscription = await subscription_dal.get_by_user_id(user_id)
    if subscription:
        subscription.tokens_remaining = int(subscription.tokens_remaining) - int(total_token_usage)
        await db.commit()
        await db.refresh(subscription)

    return {
        "used_tool": None,
        "sql_query": cleaned_query,
        "result": json.loads(query_result) if query_result.startswith("[") else query_result,
        "token_usage": token_usage,
        "refine_token_usage": refine_token_usage,
        "total_token_usage": total_token_usage,
        "refined_answer": refined_answer
    }


# @query_router.post("/audio-chat")
# async def audio_chat(
#     db: AsyncSession = Depends(get_session),
#     audio: UploadFile = File(None),
#     text: str = None,
#     token_check: bool = Depends(subscription_token_required),
# ):
#     """
#     Accepts either an audio file or text. If audio is provided, transcribe it, query the DB, and return audio. If text, return text response.
#     """
#     if audio is not None:
#         # 1. Transcribe audio to text
#         transcribed_text = await stt_service.speech_to_text(audio)
#         # 2. Query the DB using the transcribed text
#         request = QueryRequest(prompt=transcribed_text)
#         response = await query_db(request, db)
#         # 3. Convert the result to audio using TTS
#         # Use only the main result text for TTS
#         result_text = str(response["result"]) if isinstance(response, dict) and "result" in response else str(response)
#         tts_request = TTSRequest(text=result_text)
#         audio_bytes = await tts_service.text_to_speech(tts_request)
#         audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
#         return {"audio_content": audio_b64, "transcription": transcribed_text}
#     elif text is not None:
#         # 1. Query the DB using the provided text
#         request = QueryRequest(prompt=text)
#         return await query_db(request, db)
#     else:
#         raise HTTPException(status_code=400, detail="You must provide either an audio file or text.")

@query_router.post("/audio-chat")
async def audio_chat(
    db: AsyncSession = Depends(get_session),
    audio: UploadFile = File(None),
    text: str = None,
    db_url: str = None,
    user_id: str = Depends(api_key_auth)
):
    model = Gemini(id="gemini-2.0-flash", api_key=settings.gemini_api_key)
    agent = Agent(model=model)
    if audio is not None:
        transcribed_text = await stt_service.speech_to_text(audio)
        if not db_url:
            # Conversational fallback for audio
            response = agent.run(f"User: {transcribed_text}\nAI:")
            tts_request = TTSRequest(text=response.content.strip() if response and response.content else "Sorry, I couldn't generate a response.")
            audio_bytes = await tts_service.text_to_speech(tts_request)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return {"audio_content": audio_b64, "transcription": transcribed_text}
        request = QueryRequest(prompt=transcribed_text, db_url=db_url)
        stmt = select(Tool)
        result = await db.execute(stmt)
        tools = result.scalars().all()
        response = await handle_query_logic(request, user_id, db, tools, agent, api_usage_service)
        result_text = str(response.get("refined_answer", ""))
        tts_request = TTSRequest(text=result_text)
        audio_bytes = await tts_service.text_to_speech(tts_request)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {"audio_content": audio_b64, "transcription": transcribed_text}
    elif text is not None:
        if not db_url:
            # Conversational fallback for text
            response = agent.run(f"User: {text}\nAI:")
            return {"response": response.content.strip() if response and response.content else "Sorry, I couldn't generate a response."}
        request = QueryRequest(prompt=text, db_url=db_url)
        stmt = select(Tool)
        result = await db.execute(stmt)
        tools = result.scalars().all()
        return await handle_query_logic(request, user_id, db, tools, agent, api_usage_service)
    else:
        raise HTTPException(status_code=400, detail="You must provide either an audio file or text.")
