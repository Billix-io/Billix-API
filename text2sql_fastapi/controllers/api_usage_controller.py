from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from DAL_files.api_usage_dal import ApiUsageDAL
from schemas.api_usage_schemas import ApiUsageCreate, ApiUsageUpdate, ApiUsageResponse
from database import get_session
import uuid

api_usage_router = APIRouter()
usage_service = ApiUsageDAL()

@api_usage_router.post("/", response_model=ApiUsageResponse, status_code=status.HTTP_201_CREATED)
async def create_usage(
    usage: ApiUsageCreate,
    session: AsyncSession = Depends(get_session)
):
    # Attach user_id from current_user by creating a new ApiUsageCreate with user_id
  
    
    created_usage = await usage_service.create_usage_with_user_id(usage, session)
    return created_usage

@api_usage_router.get("/", response_model=List[ApiUsageResponse])
async def get_usages(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)):
    usages = await usage_service.get_usages(session, skip=skip, limit=limit)
    return usages

@api_usage_router.get("/user/{user_id}", response_model=ApiUsageResponse)
async def get_user_usages(user_id: str, session: AsyncSession = Depends(get_session)):
    usage = await usage_service.get_user_usages(user_id, session)
    if usage is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usage not found for user")
    return usage

@api_usage_router.get("/{usage_id}", response_model=ApiUsageResponse)
async def get_usage(usage_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    usage = await usage_service.get_usage(usage_id, session)
    if usage is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usage not found")
    return usage

@api_usage_router.put("/user/{user_id}", response_model=ApiUsageResponse)
async def update_usage(user_id: str, usage: ApiUsageUpdate, session: AsyncSession = Depends(get_session)):
    updated_usage = await usage_service.update_usage(user_id, usage, session)
    if updated_usage is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usage not found")
    return updated_usage

@api_usage_router.delete("/{usage_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usage(usage_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    success = await usage_service.delete_usage(usage_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usage not found")
    return 