from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from models.api_purchase_quota import ApiPurchaseQuota
from schemas.api_purchase_quota_schemas import ApiPurchaseQuotaCreate, ApiPurchaseQuotaUpdate
import uuid

class ApiPurchaseQuotaDAL:
    async def get_quota(self, quota_id: uuid.UUID, db_session: AsyncSession) -> Optional[ApiPurchaseQuota]:
        result = await db_session.execute(select(ApiPurchaseQuota).where(ApiPurchaseQuota.quota_id == quota_id))
        return result.scalar_one_or_none()

    async def get_quotas(self, db_session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ApiPurchaseQuota]:
        result = await db_session.execute(select(ApiPurchaseQuota).offset(skip).limit(limit))
        return result.scalars().all()

    async def create_quota(self, quota: ApiPurchaseQuotaCreate, db_session: AsyncSession) -> ApiPurchaseQuota:
        db_quota = ApiPurchaseQuota(
            api_name=quota.api_name,
            purchase_amount_usd=quota.purchase_amount_usd,
            notes=quota.notes
        )
        db_session.add(db_quota)
        await db_session.commit()
        await db_session.refresh(db_quota)
        return db_quota

    async def update_quota(self, quota_id: uuid.UUID, quota: ApiPurchaseQuotaUpdate, db_session: AsyncSession) -> Optional[ApiPurchaseQuota]:
        db_quota = await self.get_quota(quota_id, db_session)
        if not db_quota:
            return None
        update_data = quota.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_quota, field, value)
        await db_session.commit()
        await db_session.refresh(db_quota)
        return db_quota

    async def delete_quota(self, quota_id: uuid.UUID, db_session: AsyncSession) -> bool:
        db_quota = await self.get_quota(quota_id, db_session)
        if not db_quota:
            return False
        await db_session.delete(db_quota)
        await db_session.commit()
        return True 