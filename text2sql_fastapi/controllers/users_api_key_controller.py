from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from DAL_files.users_api_key_dal import UsersApiKeyDAL
from schemas.users_api_key_schemas import UsersApiKeyCreate, UsersApiKeyOut, UsersApiKeyUpdate, UsersApiKeyToggle
from sqlalchemy.exc import IntegrityError
from pydantic import ValidationError
from database import get_session
import secrets

users_api_key_router = APIRouter()

"""
Endpoints for managing user API keys: create, list, retrieve, enable/disable, and revoke API keys.
"""

@users_api_key_router.post("/", response_model=UsersApiKeyOut)
async def create_api_key(data: UsersApiKeyCreate, db: AsyncSession = Depends(get_session)):
    """
    Create a new API key for a user with optional expiration and active status.
    """
    try:
        dal = UsersApiKeyDAL(db)
        api_key = secrets.token_urlsafe(32)
        return await dal.create_api_key(
            user_id=data.user_id,
            api_key=api_key,
            name=data.name,
            expires_at=data.expires_at
        )
    except IntegrityError as e:
        # Handle database constraint violations (e.g., duplicate key, foreign key violations)
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="API key name already exists for this user"
            )
        elif "foreign key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database constraint violation"
            )
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        # Log the actual error for debugging but don't expose it to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the API key"
        )

@users_api_key_router.get("/user/{user_id}", response_model=list[UsersApiKeyOut])
async def list_user_api_keys(user_id: str, db: AsyncSession = Depends(get_session)):
    """
    List all API keys for a given user.
    """
    dal = UsersApiKeyDAL(db)
    return await dal.get_user_api_keys(user_id)

@users_api_key_router.get("/user/{user_id}/active", response_model=list[UsersApiKeyOut])
async def list_user_active_api_keys(user_id: str, db: AsyncSession = Depends(get_session)):
    """
    List all active API keys for a given user.
    """
    dal = UsersApiKeyDAL(db)
    return await dal.get_user_active_api_keys(user_id)

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

@users_api_key_router.put("/{api_key}/status", response_model=UsersApiKeyOut)
async def update_api_key_status(api_key: str, status: UsersApiKeyUpdate, db: AsyncSession = Depends(get_session)):
    """
    Enable or disable an API key.
    """
    dal = UsersApiKeyDAL(db)
    key = await dal.update_api_key_status(api_key, status.is_active)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key

@users_api_key_router.patch("/{api_key}/toggle", response_model=UsersApiKeyOut)
async def toggle_api_key_status(api_key: str, db: AsyncSession = Depends(get_session)):
    """
    Toggle the active status of an API key (enable if disabled, disable if enabled).
    """
    dal = UsersApiKeyDAL(db)
    key = await dal.toggle_api_key_status(api_key)
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