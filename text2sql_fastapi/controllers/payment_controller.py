from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from DAL_files.payment_dal import PaymentDAL
from schemas.payment_schemas import PaymentCreate, PaymentUpdate, PaymentResponse
from database import get_session
import uuid

payment_router = APIRouter()

@payment_router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(payment: PaymentCreate, db: Session = Depends(get_session)):
    payment_dal = PaymentDAL(db)
    try:
        db_payment = await payment_dal.create_payment(payment.model_dump())
        return PaymentResponse.model_validate(db_payment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e))

@payment_router.get("/", response_model=List[PaymentResponse])
async def get_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    payment_dal = PaymentDAL(db)
    return await payment_dal.get_payments(skip=skip, limit=limit)

@payment_router.get("/user/{user_id}", response_model=List[PaymentResponse])
async def get_user_payments(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    payment_dal = PaymentDAL(db)
    return await payment_dal.get_user_payments(user_id=user_id, skip=skip, limit=limit)

@payment_router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: uuid.UUID, db: Session = Depends(get_session)):
    payment_dal = PaymentDAL(db)
    payment = await payment_dal.get_payment(payment_id)
    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment

@payment_router.put("/{payment_id}", response_model=PaymentResponse)
async def update_payment(payment_id: uuid.UUID, payment: PaymentUpdate, db: Session = Depends(get_session)):
    payment_dal = PaymentDAL(db)
    try:
        updated_payment = await payment_dal.update_payment(payment_id, payment)
        if updated_payment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        return updated_payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@payment_router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(payment_id: uuid.UUID, db: Session = Depends(get_session)):
    payment_dal = PaymentDAL(db)
    if not await payment_dal.delete_payment(payment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        ) 