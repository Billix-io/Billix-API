from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    text: str

class TTSResponse(BaseModel):
    audio_url: Optional[str] = None
    audio_content: Optional[str] = None  # base64-encoded or direct bytes 