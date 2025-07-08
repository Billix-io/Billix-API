from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from DAL_files.user_usage_dal import UserUsageDAL
from schemas.user_usage_schemas import UserUsageCreate, UserUsageUpdate, UserUsageResponse
from database import get_session
from typing import List

user_usage_router = APIRouter(prefix="/user-usage", tags=["User Usage"])

dal = UserUsageDAL()

@user_usage_router.post("/", response_model=UserUsageResponse)
async def create_user_usage(usage: UserUsageCreate, session: AsyncSession = Depends(get_session)):
    db_usage = await dal.create_usage(usage, session)
    return db_usage

@user_usage_router.get("/{usage_id}", response_model=UserUsageResponse)
async def get_user_usage(usage_id: str, session: AsyncSession = Depends(get_session)):
    db_usage = await dal.get_usage(usage_id, session)
    if not db_usage:
        raise HTTPException(status_code=404, detail="User usage not found")
    return db_usage

@user_usage_router.get("/user/{user_id}", response_model=List[UserUsageResponse])
async def get_usages_by_user(user_id: str, session: AsyncSession = Depends(get_session)):
    usages = await dal.get_user_usages(user_id, session)
    return usages

@user_usage_router.put("/{usage_id}", response_model=UserUsageResponse)
async def update_user_usage(usage_id: str, usage: UserUsageUpdate, session: AsyncSession = Depends(get_session)):
    db_usage = await dal.update_usage(usage_id, usage, session)
    if not db_usage:
        raise HTTPException(status_code=404, detail="User usage not found")
    return db_usage

@user_usage_router.delete("/{usage_id}", response_model=bool)
async def delete_user_usage(usage_id: str, session: AsyncSession = Depends(get_session)):
    return await dal.delete_usage(usage_id, session) 