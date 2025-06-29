from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.sql import SQLTools
import os
from dotenv import load_dotenv
from controllers.ai_sql_agent import query_router
from controllers.roles_controller import roles_router
from controllers.user_controller import auth_router
from controllers.payment_controller import payment_router
from controllers.tool_controller import tool_router
from controllers.api_purchase_quota_controller import api_purchase_quota_router
from controllers.api_usage_controller import api_usage_router
from controllers.ai_stt_controller import stt_router
from controllers.ai_tts_controller import tts_router
from controllers.users_api_key_controller import users_api_key_router
from controllers.plan_controller import plan_router
from middleware import register_middleware
from contextlib import asynccontextmanager
from database import init_db
import yaml
from controllers.user_subscription_controller import user_subscription_router

load_dotenv()

# Create database tables
# Base.metadata.create_all(bind=engine)
@asynccontextmanager
async def life_span(app:FastAPI):
    print("server starting...")
    await init_db()
    yield
    print("server has been stopped")

app = FastAPI(
    title="Billix API as a Service Collection",
    description="API for converting natural language to SQL queries with token-based access control",
    version="1.0.0",
    lifespan=life_span,
    openapi_tags=[
        {"name": "query", "description": "SQL query generation endpoints"},
        {"name": "users", "description": "User authentication and management"},
        {"name": "payments", "description": "Payment processing"},
        {"name": "tools", "description": "SQL tools management"},
        {"name": "api-keys", "description": "API key management"},
        {"name": "plans", "description": "Subscription plans"},
        {"name": "user subscriptions", "description": "User subscription management"},
        {"name": "tts", "description": "Text-to-Speech services"},
        {"name": "stt", "description": "Speech-to-Text services"},
        {"name": "usage", "description": "API usage tracking"},
        {"name": "purchase-quota", "description": "API quota management"},
        {"name": "roles", "description": "User roles and permissions"},
    ]
)

# Add API Key security scheme
app.openapi_schema = None

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add API Key security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Add your API key to access protected endpoints."
        }
    }
    
    # Add security requirement to protected endpoints
    for path in openapi_schema["paths"]:
        if path.startswith("/api/v1/query"):
            for method in openapi_schema["paths"][path]:
                if method in ["post", "get", "put", "delete"]:
                    if "security" not in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

register_middleware(app)

version = "v1"
app.include_router(query_router, prefix=f"/api/{version}/query", tags=["query"])
app.include_router(roles_router, prefix=f"/api/{version}/roles", tags=["roles"])
app.include_router(auth_router, prefix=f"/api/{version}/users",tags=["users"])
app.include_router(payment_router, prefix=f"/api/{version}/payments",tags=["payments"])
app.include_router(query_router, prefix=f"/api/{version}/query", tags=["query"])
app.include_router(tool_router, prefix=f"/api/{version}/tools", tags=["tools"])
app.include_router(api_purchase_quota_router, prefix=f"/api/{version}/purchase-quota", tags=["purchase-quota"])
app.include_router(api_usage_router, prefix=f"/api/{version}/usage", tags=["usage"])
app.include_router(tts_router, prefix=f"/api/{version}/tts", tags=["tts"])
app.include_router(stt_router, prefix=f"/api/{version}/stt", tags=["stt"])
app.include_router(user_subscription_router, prefix=f"/api/{version}/subscriptions", tags=["user subscriptions"])
app.include_router(users_api_key_router, prefix=f"/api/{version}/api-keys", tags=["api-keys"])
app.include_router(plan_router, prefix=f"/api/{version}/plans", tags=["plans"])

# class QueryRequest(BaseModel):
#     db_url: str
#     query: str



# Load Swagger YAML - using correct file path
# swagger_file_path = os.path.join(os.path.dirname(__file__), "swagger.yaml")
# try:
#     with open(swagger_file_path, "r") as file:
#         swagger_yaml = yaml.safe_load(file)
        
#     # Custom OpenAPI schema
#     def custom_openapi():
#         if app.openapi_schema:
#             return app.openapi_schema
#         app.openapi_schema = swagger_yaml
#         return app.openapi_schema

#     app.openapi = custom_openapi
#     print(f"Swagger documentation loaded from {swagger_file_path}")
# except Exception as e:
#     print(f"Error loading Swagger YAML: {e}")
