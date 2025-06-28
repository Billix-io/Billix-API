from sqlalchemy.future import select
from models.plan import Plan

class PlanDAL:
    def __init__(self, db_session):
        self.db_session = db_session

    async def create_plan(self, name, description, price, tokens):
        plan = Plan(name=name, description=description, price=price, tokens=tokens)
        self.db_session.add(plan)
        await self.db_session.commit()
        await self.db_session.refresh(plan)
        return plan

    async def get_plan(self, plan_id):
        return await self.db_session.get(Plan, plan_id)

    async def list_plans(self):
        result = await self.db_session.execute(select(Plan))
        return result.scalars().all() 