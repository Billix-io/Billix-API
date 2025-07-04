import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from schemas.invoice_schemas import InvoiceData
import fitz
import base64

"""
Data Access Layer for invoice extraction using LLMs and document parsing.
Handles classification, extraction from text, PDF, and images.
"""

class SimpleInvoiceExtractor:
    """
    Extracts invoice data from text, PDF, or images using LLMs and prompt templates.
    """
    def __init__(self, groq_api_key: str):
        """
        Initialize the extractor with a Groq API key and set up prompt templates.
        """
        self.model = ChatGroq(
            temperature=0.1,
            groq_api_key=groq_api_key,
            model_name="meta-llama/llama-4-scout-17b-16e-instruct",
        )

        self.text_extract_prompt_template =self.image_text_extract_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract all text content from this document exactly as it appears.\n      Maintain the original layout and formatting as much as possible.\n      Pay special attention to:\n      1. Table structures and numerical data\n      2. Invoice-specific fields like dates, amounts, and IDs\n      3. Vendor and customer information\n      4. Line items with quantities and prices"),

            ("human",
                [
                    {"type":"text", "text": "Extract all text from this document with high accuracy:"},
                    {"type": "image_url", "image_url": {"url": "{image_url}"}}
                ])
        ])

        self.prompt_template = ChatPromptTemplate.from_messages([
                        ("system", """
           You are an expert invoice data extraction and financial auditing assistant that works very quickly and efficiently. Extract all key information from the provided {{documentType}} and perform financial validation. Return **only** a valid JSON object with no extra text.

Extract the following key fields:
1. Basic invoice details: number, date, due date, reference codes
2. Vendor information: name, address, tax ID, contact info
3. Customer information: name, address, contact info
4. Line items with original field names:
   - **Preserve original field labels as used in the document**. For example:
     - If the document uses "Rate", use `"rate"` in the JSON.
     - If it uses "Unit Price", use `"unitPrice"`.
     - If it uses "Price", use `"price"`.
   - The same rule applies for "Qty" vs "Quantity".
   - Do **not** normalize the keys — use what is in the source.
5. Financial details: subtotal, discounts, taxes, shipping, total, currency
6. Payment information: method, terms, bank details, payment link if present

Additional instructions:
- Identify the primary language using ISO 639-1
- Identify the likely country based on address/currency
- Assign realistic confidence scores (0–100) for major fields
- Provide an overall extraction confidence score
- If vendor name is missing, suggest 2–3 likely vendor types
- If business category is unclear, suggest 2–3 possibilities with confidence scores (50–80 only)
- Do not suggest vendor types if vendor name is present
- If invoice is from a business to a customer, classify it as an outgoing/sales invoice

FINANCIAL VALIDATION:
- Ensure line item amount = quantity × unit price/rate
- Ensure subtotal = sum of line items
- Ensure total = subtotal + tax + shipping – discounts
- Flag any inconsistencies or rounding issues
- Validate tax based on country

TAX ACCOUNTING:
- Extract all tax-related fields: tax rates, tax names (VAT, GST, etc.)
- Identify any exemptions or zero-rated items
- If multi-tax system (like India), break down components (CGST, SGST, etc.)

PAYMENT INFO:
- Extract payment method, terms (e.g., Net 30), and any banking/payment link info
- Capture any early discount or late penalties if mentioned

Return JSON in this format (use source labels in `lineItems`):

{{
  "invoiceNumber": "string",
  "date": "string",
  "dueDate": "string",
  "vendor": {{
    "name": "string",
    "address": "string",
    "taxId": "string"
  }},
  "customer": {{
    "name": "string",
    "address": "string"
  }},
  "lineItems": [
    {{
      "description": "string",
      "qty"/"quantity": "string",
      "rate"/"unitPrice"/"price": "string",
      "amount": "string",
      "taxRate": "string"
    }}
  ],
  "financials": {{
    "subtotal": "string",
    "discount": "string",
    "tax": "string",
    "taxRate": "string",
    "shipping": "string",
    "total": "string",
    "currency": "string",
    "taxName": "string",
    "additionalTaxes": [
      {{
        "name": "string",
        "rate": "string",
        "amount": "string"
      }}
    ]
  }},
  "payment": {{
    "method": "string",
    "terms": "string",
    "bankDetails": {{
      "accountNumber": "string",
      "routingNumber": "string",
      "iban": "string",
      "swift": "string",
      "bankName": "string"
    }},
    "paymentLink": "string",
    "earlyDiscount": {{
      "percentage": "string",
      "days": "string"
    }},
    "latePenalty": {{
      "percentage": "string",
      "days": "string"
    }}
  }},
  "meta": {{
    "language": "string (ISO 639-1 code)",
    "languageName": "string",
    "country": "string",
    "countryCode": "string",
    "region": "string",
    "confidence": {{
      "overall": 0,
      "fields": {{}}
    }},
    "audit": {{
      "status": "PASS",
      "issues": [
        {{
          "type": "string",
          "severity": "LOW",
          "description": "string",
          "affectedFields": ["string"]
        }}
      ],
      "taxCompliance": {{
        "status": "COMPLIANT",
        "details": "string"
      }},
      "fraudIndicators": {{
        "score": 0,
        "flags": ["string"]
      }}
    }},
    "suggestions": {{
      "invoiceType": "SALES",
      "categories": [
        {{"name": "string", "confidence": 60}},
        {{"name": "string", "confidence": 55}}
      ],
      "vendorTypes": [],
      "selectedCategory": null,
      "selectedVendorType": null
    }}
  }}
}}

"""),
            ("human", "Extract invoice data from this text and return structured JSON:\n{text}")
        ])

    def classify_document(self, text: str) -> str:
        """
        Classify the document type (invoice, receipt, PO, etc.) based on text patterns.
        """
        lower_text = text.lower()
        invoice_patterns = [
            "invoice", "bill to", "factura", "rechnung", "facture", "fattura", "发票", "インボイス",
            "فاتورة", "חשבונית", "счет", "tax invoice", "billing statement", "payment due",
            "invoice number", "invoice no", "invoice #", "inv #", "inv no", "invoice date"
        ]
        receipt_patterns = [
            "receipt", "payment received", "paid", "payment confirmation", "proof of payment",
            "recibo", "quittung", "reçu", "ricevuta", "收据", "領収書", "إيصال", "קבלה", "квитанция",
            "thank you for your purchase", "cash receipt", "payment receipt"
        ]
        po_patterns = [
            "purchase order", "p.o.", "p/o", "order confirmation", "order form",
            "orden de compra", "bestellung", "bon de commande", "ordine d'acquisto", "采购订单",
            "注文書", "أمر شراء", "הזמנת רכש", "заказ на покупку"
        ]
        quote_patterns = [
            "quote", "estimate", "quotation", "proposal", "pro forma", "proforma",
            "presupuesto", "angebot", "devis", "preventivo", "报价", "見積もり",
            "عرض أسعار", "הצעת מחיר", "коммерческое предложение"
        ]
        statement_patterns = [
            "statement", "account statement", "statement of account", "monthly statement",
            "estado de cuenta", "kontoauszug", "relevé de compte", "estratto conto", "对账单",
            "取引明細書", "كشف حساب", "דף חשבון", "выписка по счету"
        ]
        creditNote_patterns = [
            "credit note", "credit memo", "credit memorandum", "refund",
            "nota de crédito", "gutschrift", "note de crédit", "nota di credito", "贷记通知单",
            "クレジットノート", "إشعار دائن", "הודעת זיכוי", "кредитное авизо"
        ]
        for pattern in invoice_patterns:
            if pattern in lower_text:
                return "invoice"
        for pattern in receipt_patterns:
            if pattern in lower_text:
                return "receipt"
        for pattern in po_patterns:
            if pattern in lower_text:
                return "purchase_order"
        for pattern in quote_patterns:
            if pattern in lower_text:
                return "quote"
        for pattern in statement_patterns:
            if pattern in lower_text:
                return "statement"
        for pattern in creditNote_patterns:
            if pattern in lower_text:
                return "credit_note"
        if (
            ("total" in lower_text and ("due" in lower_text or "amount" in lower_text)) or
            ("payment" in lower_text and "terms" in lower_text) or
            ("tax" in lower_text and "subtotal" in lower_text)
        ):
            return "invoice"
        import re
        if re.search(r"inv[^a-z]", lower_text) and re.search(r"\d{4,}", lower_text):
            return "invoice"
        return "invoice"    


    def extract_invoice_fromate_from_text(self, text: str, doctype: str):
        """
        Extract structured invoice data from raw text using the LLM and prompt template.
        """
        try:
            # Create processing chain with metadata capture
            chain = (
                self.prompt_template 
                | self.model 
                | {"data": JsonOutputParser(), "metadata": lambda x: x}
            )
            
            # Process text with document type context and token usage tracking
            result = chain.invoke(
                {"text": text, "documentType": doctype},
                config={"return_token_usage": True}
            )
            
            # Extract token usage metadata
       
            usage = result["metadata"].usage_metadata
            
            # Return structured data with token usage
            return result["data"]
                
        
        except Exception as e:
            print(f"Error processing text: {e}")
            raise
    
    def extract_from_pdf_bytes(self, pdf_bytes: bytes) -> InvoiceData:
        """
        Extract invoice data from PDF bytes using OCR and LLM extraction.
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.page_count == 0:
            raise ValueError("No pages found in PDF")
        page = doc.load_page(0)
        pix = page.get_pixmap()
        img_bytes = pix.tobytes("png")
        base64_image = base64.b64encode(img_bytes).decode("utf-8")
        return self.extract_from_base64_image(base64_image)

    def extract_from_base64_image(self, base64_image: str) -> InvoiceData:
        """
        Extract invoice data from a base64-encoded image using OCR and LLM extraction.
        """
        try:
            str_parser = StrOutputParser()
            chain = (
            self.text_extract_prompt_template 
            | self.model 
            | {"text": StrOutputParser(), "metadata": lambda x: x}
            )
            result = chain.invoke({"image_url": f"data:image/png;base64,{base64_image}"},config={"return_token_usage": True})
            
       
            token_usage=result["metadata"].usage_metadata
            
            return {"text":result["text"]}
            
        except Exception as e:
            print(f"Error processing base64 image: {e}")
            raise