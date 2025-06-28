from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from models.payment import Payment
from schemas.payment_schemas import PaymentCreate, PaymentUpdate
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

class PaymentDAL:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_payment(self, payment_id: uuid.UUID) -> Optional[Payment]:
        result = await self.db_session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payments(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        result = await self.db_session.execute(
            select(Payment).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_user_payments(self, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Payment]:
        result = await self.db_session.execute(
            select(Payment).where(Payment.user_id == user_id).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create_payment(self, data: dict) -> Payment:
        payment = Payment(**data)
        try:
            self.db_session.add(payment)
            await self.db_session.commit()
            await self.db_session.refresh(payment)
            return payment
        except IntegrityError:
            await self.db_session.rollback()
            raise ValueError("Payment with this transaction_id already exists")

    async def update_payment(self, payment_id: uuid.UUID, payment: PaymentUpdate) -> Optional[Payment]:
        db_payment = await self.get_payment(payment_id)
        if not db_payment:
            return None

        update_data = payment.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment, field, value)

        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_payment)
            return db_payment
        except IntegrityError:
            await self.db_session.rollback()
            raise ValueError("Transaction ID already exists")

    async def delete_payment(self, payment_id: uuid.UUID) -> bool:
        db_payment = await self.get_payment(payment_id)
        if not db_payment:
            return False
        
        await self.db_session.delete(db_payment)
        await self.db_session.commit()
        return True

    @staticmethod
    async def user_has_successful_payment(user_id: uuid.UUID, db_session: AsyncSession) -> bool:
        from models.payment import PaymentStatus
        result = await db_session.execute(
            select(Payment).where(
                Payment.user_id == user_id,
                Payment.status == PaymentStatus.SUCCEEDED
            )
        )
        payment = result.scalar_one_or_none()
        return payment is not None 