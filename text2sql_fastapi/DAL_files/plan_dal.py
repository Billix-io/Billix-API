from sqlalchemy.future import select
from models.plan import Plan
from schemas.plan_schemas import PlanCreate

"""
Data Access Layer for subscription plan operations: create, retrieve, and list plans.
"""

class PlanDAL:
    """
    Data Access Layer for subscription plan operations.
    """
    def __init__(self, db_session):
        """
        Initialize with a database session.
        """
        self.db_session = db_session

    async def create_plan(self, data:PlanCreate):
        """
        Create a new subscription plan in the database.
        """
        plan = Plan(**data.model_dump())
        self.db_session.add(plan)
        await self.db_session.commit()
        await self.db_session.refresh(plan)
        return plan

    async def get_plan(self, plan_id):
        """
        Retrieve a subscription plan by its ID.
        """
        return await self.db_session.get(Plan, plan_id)

    async def list_plans(self):
        """
        List all subscription plans in the database.
        """
        result = await self.db_session.execute(select(Plan))
        return result.scalars().all() 