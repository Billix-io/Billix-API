from fastapi.security import HTTPBearer
from fastapi import Request, status, Depends, Header
from fastapi.security.http import HTTPAuthorizationCredentials
from utils import decode_token
from fastapi.exceptions import HTTPException
from database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from DAL_files.roles_dal import RoleDAL
from DAL_files.users_api_key_dal import UsersApiKeyDAL
from typing import List, Any, Optional
from redis_store import token_in_blocklist
from DAL_files.payment_dal import PaymentDAL
from datetime import datetime
from models.user_subscription import UserSubscription
from models.user_usage import UserUsage
from models.users_api_key import UsersApiKey


from sqlalchemy.future import select
from models.users_api_key import UsersApiKey
from models.api_usage import ApiUsage
from models.plan import Plan

async def chat_usage_checker(
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: AsyncSession = Depends(get_session)
):
    """
    Dependency to check if the user (by API key) has not exceeded their chat usage limit.
    Raises HTTPException if not allowed.
    Returns user_id if allowed.
    """
    # 1. Check API key
    result = await session.execute(
        select(UsersApiKey).where(
            UsersApiKey.api_key == x_api_key,
            UsersApiKey.is_active == True
        )
    )

    api_key_obj = result.scalar_one_or_none()
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")
    user_id = api_key_obj.user_id

    # 2. Get API usage for user
    result = await session.execute(
        select(ApiUsage).where(ApiUsage.userId == user_id)
    )
    usage_obj = result.scalar_one_or_none()
    if not usage_obj:
        raise HTTPException(status_code=404, detail="API usage not found for user")
    chat_usage = usage_obj.chatUsage

    # 3. Get subscription for user
    result = await session.execute(
        select(UserSubscription).where(UserSubscription.userId == user_id)
    )
    subscription_obj = result.scalar_one_or_none()
    if not subscription_obj:
        raise HTTPException(status_code=404, detail="Subscription not found for user")
    plan_id = subscription_obj.planId

    # 4. Get plan for plan_id
    result = await session.execute(
        select(Plan).where(Plan.id == plan_id)
    )
    plan_obj = result.scalar_one_or_none()
    if not plan_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    chat_limit = plan_obj.chatLimit

    # 5. Compare usage with plan limit
    if chat_limit is not None and chat_usage >= chat_limit:
        raise HTTPException(status_code=403, detail="Chat usage limit reached")

    return user_id

async def invoice_usage_checker(
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: AsyncSession = Depends(get_session)
):
    """
    Dependency to check if the user (by API key) has not exceeded their invoice usage limit.
    Raises HTTPException if not allowed.
    Returns user_id if allowed.
    """
    # 1. Check API key
    result = await session.execute(
        select(UsersApiKey).where(
            UsersApiKey.api_key == x_api_key,
            UsersApiKey.is_active == True
        )
    )
    api_key_obj = result.scalar_one_or_none()
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid API key")
    user_id = api_key_obj.user_id

    # 2. Get API usage for user
    result = await session.execute(
        select(ApiUsage).where(ApiUsage.userId == user_id)
    )
    usage_obj = result.scalar_one_or_none()
    if not usage_obj:
        raise HTTPException(status_code=404, detail="API usage not found for user")
    invoice_usage = usage_obj.invoiceUsage

    # 3. Get subscription for user
    result = await session.execute(
        select(UserSubscription).where(UserSubscription.userId == user_id)
    )
    subscription_obj = result.scalar_one_or_none()
    if not subscription_obj:
        raise HTTPException(status_code=404, detail="Subscription not found for user")
    plan_id = subscription_obj.planId

    # 4. Get plan for plan_id
    result = await session.execute(
        select(Plan).where(Plan.id == plan_id)
    )
    plan_obj = result.scalar_one_or_none()
    if not plan_obj:
        raise HTTPException(status_code=404, detail="Plan not found")
    invoice_limit = plan_obj.invoiceLimit

    # 5. Compare usage with plan limit
    if invoice_limit is not None and invoice_usage >= invoice_limit:
        raise HTTPException(status_code=403, detail="Invoice usage limit reached")

    return user_id