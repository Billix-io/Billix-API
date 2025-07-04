from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from DAL_files.help_and_support_dal import (create_help_and_support, get_help_and_support_by_id, get_all_help_and_support, update_help_and_support_status)
from schemas.help_and_support_schemas import HelpAndSupportCreate, HelpAndSupportResponse
from dependencies import RoleChecker, get_current_user, AccessTokenBearer
from schemas.user_schemas import UserCreate, UserUpdate, UserLogin, UserBase
from dependencies import get_session
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
help_support_router = APIRouter()

"""
Help and Support ticket endpoints for user support requests and ticket management.
Includes ticket creation, retrieval, listing, and status update.
"""

@help_support_router.post("/{user_id}", response_model=HelpAndSupportResponse)
async def create_ticket(help_data: HelpAndSupportCreate, user_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_session)):
    """
    Create a new help/support ticket for a user and send a confirmation email.
    """
    ticket = await create_help_and_support(db, help_data.model_dump(), user_id)
    # Prepare the email
    html_content = f"""
    <html>
      <body>
        <h2>New Support Ticket Created</h2>
        <p><strong>Ticket Number:</strong> {ticket.id}</p>
        <p><strong>Subject:</strong> Billix Help and Support</p>
        <p><strong>Description:</strong> {help_data.message}</p>
        <p>We'll get back to you soon!</p>
      </body>
    </html>
    """

    message = MessageSchema(
        subject="Ticket Received ✔",
        recipients=[help_data.email],  # replace with real email
        body=html_content,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return ticket

@help_support_router.get("/{ticket_id}", response_model=HelpAndSupportResponse)
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_session)):
    """
    Retrieve a help/support ticket by its ID.
    """
    ticket = await get_help_and_support_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@help_support_router.get("/", response_model=list[HelpAndSupportResponse])
async def list_tickets(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_session)):
    """
    List all help/support tickets with optional pagination.
    """
    return await get_all_help_and_support(db, skip, limit)

@help_support_router.patch("/{ticket_id}/status", response_model=HelpAndSupportResponse)
async def update_status(ticket_id: int, status: str, db: AsyncSession = Depends(get_session)):
    """
    Update the status of a help/support ticket by its ID.
    """
    ticket = await update_help_and_support_status(db, ticket_id, status)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket