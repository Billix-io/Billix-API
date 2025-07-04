"""
Pydantic schemas for Text-to-Speech (TTS) requests and responses.
"""
from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    """
    Schema for a TTS request, containing the input text to synthesize.
    """
    text: str

class TTSResponse(BaseModel):
    """
    Schema for a TTS response, containing the audio URL or content.
    """
    audio_url: Optional[str] = None
    audio_content: Optional[str] = None  # base64-encoded or direct bytes 