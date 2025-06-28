from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from models.user_subscription import UserSubscription
from models.plan import Plan
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

class UserSubscriptionDAL:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSubscription]:
        result = await self.db_session.execute(
            select(UserSubscription).where(UserSubscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def has_minimum_tokens(self, user_id: uuid.UUID, min_tokens: int) -> bool:
        subscription = await self.get_by_user_id(user_id)
        if not subscription:
            return False
        return int(subscription.tokens_remaining) >= min_tokens

    async def create_subscription(self, data: dict):
        # Fetch the plan to get the number of tokens
        result = await self.db_session.execute(select(Plan).where(Plan.plan_id == data['plan_id']))
        plan = result.scalar_one_or_none()
        if not plan:
            raise ValueError("Plan not found")
        
        # Add calculated fields to the data
        data.update({
            'subscription_id': uuid.uuid4(),
            'total_tokens_purchased': plan.tokens,
            'tokens_remaining': plan.tokens,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        subscription = UserSubscription(**data)
        self.db_session.add(subscription)
        await self.db_session.commit()
        await self.db_session.refresh(subscription)
        return subscription

    async def update_subscription(self, user_id: uuid.UUID, update_data: dict):
        subscription = await self.get_by_user_id(user_id)
        if not subscription:
            return None
        for key, value in update_data.items():
            setattr(subscription, key, value)
        await self.db_session.commit()
        await self.db_session.refresh(subscription)
        return subscription 