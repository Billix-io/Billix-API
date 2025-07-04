"""
Main entry point for the Text to SQL FastAPI application.
Initializes the FastAPI app, sets up routers, middleware, and custom OpenAPI schema.
"""
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
from controllers.invoice_controller import invoice_router
from controllers.help_and_support_controller import help_support_router

load_dotenv()

# Create database tables
# Base.metadata.create_all(bind=engine)
@asynccontextmanager
async def life_span(app:FastAPI):
    """
    Application lifespan event handler. Initializes the database on startup.
    """
    print("server starting...")
    await init_db()
    yield
    print("server has been stopped")

app = FastAPI(
    title="Text to SQL API",
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
    """
    Customizes the OpenAPI schema to add API Key security scheme and security requirements for protected endpoints.
    """
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
app.include_router(user_subscription_router, prefix=f"/api/{version}/subscriptions", tags=["user subscriptions"])
app.include_router(users_api_key_router, prefix=f"/api/{version}/api-keys", tags=["api-keys"])
app.include_router(plan_router, prefix=f"/api/{version}/plans", tags=["plans"])
app.include_router(invoice_router,prefix=f"/api/{version}/invoice", tags=["invoices"])
app.include_router(help_support_router,prefix=f"/api/{version}/help-support", tags=["Help and Support"])


