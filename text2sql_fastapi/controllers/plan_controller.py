from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from DAL_files.plan_dal import PlanDAL
from schemas.plan_schemas import PlanCreate, PlanOut
from database import get_session

plan_router = APIRouter()

"""
Endpoints for creating and listing subscription plans.
"""

@plan_router.post("/", response_model=PlanOut)
async def create_plan(plan: PlanCreate, db: AsyncSession = Depends(get_session)):
    """
    Create a new subscription plan.
    """
    dal = PlanDAL(db)
    return await dal.create_plan(plan)

@plan_router.get("/", response_model=list[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_session)):
    """
    List all available subscription plans.
    """
    dal = PlanDAL(db)
    return await dal.list_plans() 