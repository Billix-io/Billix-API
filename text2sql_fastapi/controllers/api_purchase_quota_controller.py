from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from DAL_files.api_purchase_quota_dal import ApiPurchaseQuotaDAL
from schemas.api_purchase_quota_schemas import ApiPurchaseQuotaCreate, ApiPurchaseQuotaUpdate, ApiPurchaseQuotaResponse
from database import get_session
import uuid

api_purchase_quota_router = APIRouter()
quota_service = ApiPurchaseQuotaDAL()

@api_purchase_quota_router.post("/", response_model=ApiPurchaseQuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_quota(quota: ApiPurchaseQuotaCreate, session: AsyncSession = Depends(get_session)):
    created_quota = await quota_service.create_quota(quota, session)
    return created_quota

@api_purchase_quota_router.get("/", response_model=List[ApiPurchaseQuotaResponse])
async def get_quotas(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)):
    quotas = await quota_service.get_quotas(session, skip=skip, limit=limit)
    return quotas

@api_purchase_quota_router.get("/{quota_id}", response_model=ApiPurchaseQuotaResponse)
async def get_quota(quota_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    quota = await quota_service.get_quota(quota_id, session)
    if quota is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota not found")
    return quota

@api_purchase_quota_router.put("/{quota_id}", response_model=ApiPurchaseQuotaResponse)
async def update_quota(quota_id: uuid.UUID, quota: ApiPurchaseQuotaUpdate, session: AsyncSession = Depends(get_session)):
    updated_quota = await quota_service.update_quota(quota_id, quota, session)
    if updated_quota is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota not found")
    return updated_quota

@api_purchase_quota_router.delete("/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota(quota_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    success = await quota_service.delete_quota(quota_id, session)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quota not found")
    return 