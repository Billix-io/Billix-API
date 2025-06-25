from fastapi import APIRouter, UploadFile, File, HTTPException
from DAL_files.stt_dal import STTDAL

stt_router = APIRouter()
stt_service = STTDAL()

@stt_router.post("/stt")
async def speech_to_text_endpoint(audio: UploadFile = File(...)):
    try:
        text = await stt_service.speech_to_text(audio)
        return {"transcription": text}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))