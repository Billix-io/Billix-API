from fastapi import APIRouter, HTTPException
from schemas.tts_schemas import TTSRequest, TTSResponse
from DAL_files.tts_dal import TTSDAL
import base64

tts_router = APIRouter()
tts_service = TTSDAL()

@tts_router.post("/tts", response_model=TTSResponse)
async def text_to_speech(tts_request: TTSRequest):
    try:
        audio_bytes = await tts_service.text_to_speech(tts_request)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return TTSResponse(audio_content=audio_b64)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 