from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from DAL_files.users_api_key_dal import UsersApiKeyDAL
from schemas.users_api_key_schemas import UsersApiKeyCreate, UsersApiKeyOut
from database import get_session
import secrets

users_api_key_router = APIRouter()

"""
Endpoints for managing user API keys: create, list, retrieve, and revoke API keys.
"""

@users_api_key_router.post("/", response_model=UsersApiKeyOut)
async def create_api_key(data: UsersApiKeyCreate, db: AsyncSession = Depends(get_session)):
    """
    Create a new API key for a user with optional expiration.
    """
    dal = UsersApiKeyDAL(db)
    api_key = secrets.token_urlsafe(32)
    return await dal.create_api_key(user_id=data.user_id, api_key=api_key,name=data.name , expires_at=data.expires_at)

@users_api_key_router.get("/user/{user_id}", response_model=list[UsersApiKeyOut])
async def list_user_api_keys(user_id: str, db: AsyncSession = Depends(get_session)):
    """
    List all API keys for a given user.
    """
    dal = UsersApiKeyDAL(db)
    return await dal.get_user_api_keys(user_id)

@users_api_key_router.get("/{api_key}", response_model=UsersApiKeyOut)
async def get_api_key(api_key: str, db: AsyncSession = Depends(get_session)):
    """
    Retrieve an API key by its value.
    """
    dal = UsersApiKeyDAL(db)
    key = await dal.get_api_key(api_key)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key

@users_api_key_router.delete("/{api_key}", response_model=UsersApiKeyOut)
async def revoke_api_key(api_key: str, db: AsyncSession = Depends(get_session)):
    """
    Revoke (delete) an API key by its value.
    """
    dal = UsersApiKeyDAL(db)
    key = await dal.revoke_api_key(api_key)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key 