from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from DAL_files.user_subscription_dal import UserSubscriptionDAL
from database import get_session
import uuid
from schemas.user_subscription_schemas import UserSubscriptionCreate, UserSubscriptionUpdate, UserSubscriptionResponse

user_subscription_router = APIRouter()

@user_subscription_router.post("/", response_model=UserSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(subscription_data: UserSubscriptionCreate, session: AsyncSession = Depends(get_session)):
    dal = UserSubscriptionDAL(session)
    subscription = await dal.create_subscription(subscription_data.dict())
    return subscription

@user_subscription_router.get("/user/{user_id}", response_model=UserSubscriptionResponse)
async def get_subscription(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    dal = UserSubscriptionDAL(session)
    subscription = await dal.get_by_user_id(user_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription

@user_subscription_router.put("/user/{user_id}", response_model=UserSubscriptionResponse)
async def update_subscription(user_id: uuid.UUID, update_data: UserSubscriptionUpdate, session: AsyncSession = Depends(get_session)):
    dal = UserSubscriptionDAL(session)
    subscription = await dal.update_subscription(user_id, update_data.dict(exclude_unset=True))
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return subscription 