from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from models.payment import Payment
from schemas.payment_schemas import PaymentCreate, PaymentUpdate
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

class PaymentDAL:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_payment(self, payment_id: uuid.UUID) -> Optional[Payment]:
        return self.db_session.query(Payment).filter(Payment.payment_id == payment_id).first()

    def get_payments(self, skip: int = 0, limit: int = 100) -> List[Payment]:
        return self.db_session.query(Payment).offset(skip).limit(limit).all()

    def get_user_payments(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Payment]:
        return self.db_session.query(Payment)\
            .filter(Payment.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def create_payment(self, payment: PaymentCreate) -> Payment:
        db_payment = Payment(
            plan_type=payment.plan_type,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            provider=payment.provider,
            transaction_id=payment.transaction_id,
            user_id=payment.user_id
        )
        try:
            self.db_session.add(db_payment)
            self.db_session.commit()
            self.db_session.refresh(db_payment)
            return db_payment
        except IntegrityError:
            self.db_session.rollback()
            raise ValueError("Payment with this transaction_id already exists")

    def update_payment(self, payment_id: uuid.UUID, payment: PaymentUpdate) -> Optional[Payment]:
        db_payment = self.get_payment(payment_id)
        if not db_payment:
            return None

        update_data = payment.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment, field, value)

        try:
            self.db_session.commit()
            self.db_session.refresh(db_payment)
            return db_payment
        except IntegrityError:
            self.db_session.rollback()
            raise ValueError("Transaction ID already exists")

    def delete_payment(self, payment_id: uuid.UUID) -> bool:
        db_payment = self.get_payment(payment_id)
        if not db_payment:
            return False
        
        self.db_session.delete(db_payment)
        self.db_session.commit()
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