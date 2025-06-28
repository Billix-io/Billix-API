from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict

class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class InvoiceLineItem(BaseModel):
    id: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unitPrice: Optional[float] = None
    totalPrice: Optional[float] = None
    taxRate: Optional[float] = None
    taxAmount: Optional[float] = None
    discount: Optional[float] = None
    productSku: Optional[str] = None
    notes: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None

class InvoiceData(BaseModel):
    invoiceNumber: Optional[str] = None
    status: Optional[InvoiceStatus] = None
    issueDate: Optional[datetime] = None
    dueDate: Optional[datetime] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    vendorName: Optional[str] = None
    customerName: Optional[str] = None
    notes: Optional[str] = None
    categoryId: Optional[str] = None
    lineItems: Optional[List[InvoiceLineItem]] = None

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.strftime('%Y-%m-%d')}
    ) 

class InvoiceTextRequest(BaseModel):
    text: str
   