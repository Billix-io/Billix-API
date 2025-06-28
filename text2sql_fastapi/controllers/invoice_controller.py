from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import os
from DAL_files.invoice_dal import SimpleInvoiceExtractor
from schemas.invoice_schemas import InvoiceTextRequest
import tempfile
import re


invoice_router = APIRouter()
invoice_extractor = SimpleInvoiceExtractor(groq_api_key="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")

@invoice_router.post("/extract/invoice")
def extract_invoice(request: InvoiceTextRequest):
    """
    Classify document type and extract invoice data from provided text.
    """
    try:
        doc_type = invoice_extractor.classify_document(request.text)
        print("-----------------",doc_type,"-------------")
        invoice_data = invoice_extractor.extract_invoice_fromate_from_text(request.text, doc_type)
        return invoice_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @invoice_router.post("/extract/pdf-text")
# async def extract_pdf_text(file: UploadFile = File(...)):
#     """
#     Extract text from a PDF file using LlamaParse.
#     """
#     try:
#         api_key = "llx-npVcby1qgzg1xKfvNJaWfprYXYb0YLK0OdDwpWJyYVg0OU8Y"
#         parsingInstructionSpaceContent = None  # Set your parsing instructions here if needed

#         # Save the uploaded file to a temporary location
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
#             contents = await file.read()
#             temp_file.write(contents)
#             temp_file.flush()
#             temp_path = temp_file.name

#         # Create an instance of LlamaParse with the API key, result_type as "markdown", and parsing instructions
#         withSpaceContent = LlamaParse(
#             result_type="text",
#             api_key=api_key,
#             fast_mode=True
#         )

#         # Load and parse the document
#         parsed_content = withSpaceContent.load_data(temp_path)

#         text = "\n".join(
#             "\n".join(
#                 re.sub(r'\s+', ' ', line).strip()
#                 for line in doc.text.splitlines()
#             )
#             for doc in parsed_content
#         )

#         # Clean up the temp file
#         os.remove(temp_path)

#         return {"text": text}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@invoice_router.post("/extract/pdf-image-text")
async def extract_pdf_image_text(file: UploadFile = File(...)):
    """
    Extract invoice data from an uploaded PDF or image file (in-memory, no temp file).
    """
    try:
        suffix = os.path.splitext(file.filename)[1].lower()
        file_bytes = file.file.read()
       
        if suffix == ".pdf":
            invoice_data = invoice_extractor.extract_from_pdf_bytes(file_bytes)
        elif suffix in [".jpg", ".jpeg", ".png", ".bmp"]:
            import base64
            base64_image = base64.b64encode(file_bytes).decode("utf-8")
            invoice_data = invoice_extractor.extract_from_base64_image(base64_image)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")
        return invoice_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 