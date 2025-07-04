from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.help_and_support import HelpAndSupport

"""
Async CRUD operations for HelpAndSupport tickets in the database.
"""

async def create_help_and_support(db: AsyncSession, help_data, user_id):
    """
    Create a new help/support ticket for a user.
    """
    help_ticket = HelpAndSupport(**help_data, user_id=user_id)
    db.add(help_ticket)
    await db.commit()
    await db.refresh(help_ticket)
    return help_ticket

async def get_help_and_support_by_id(db: AsyncSession, ticket_id: int):
    """
    Retrieve a help/support ticket by its ID.
    """
    result = await db.execute(select(HelpAndSupport).where(HelpAndSupport.id == ticket_id))
    return result.scalars().first()

async def get_all_help_and_support(db: AsyncSession, skip: int = 0, limit: int = 100):
    """
    List all help/support tickets with optional pagination.
    """
    result = await db.execute(select(HelpAndSupport).offset(skip).limit(limit))
    return result.scalars().all()

async def update_help_and_support_status(db: AsyncSession, ticket_id: int, status: str):
    """
    Update the status of a help/support ticket by its ID.
    """
    result = await db.execute(select(HelpAndSupport).where(HelpAndSupport.id == ticket_id))
    ticket = result.scalars().first()
    if ticket:
        ticket.status = status
        await db.commit()
        await db.refresh(ticket)
    return ticket