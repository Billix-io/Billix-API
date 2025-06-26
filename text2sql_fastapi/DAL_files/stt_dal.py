import os
from elevenlabs.client import ElevenLabs
from fastapi import HTTPException, UploadFile
from io import BytesIO
from config import settings

class STTDAL:
    async def speech_to_text(self, audio_file: UploadFile) -> str:
        client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        try:
            audio_data = BytesIO(await audio_file.read())
            transcription = client.speech_to_text.convert(
                file=audio_data,
                model_id="scribe_v1",
                tag_audio_events=True,
                language_code='eng',
                diarize=True,
            )
            # Handle different possible return types
            if isinstance(transcription, dict) and "text" in transcription:
                return transcription["text"]
            elif hasattr(transcription, "text"):
                return transcription.text
            elif isinstance(transcription, str):
                return transcription
            else:
                raise Exception(f"Unexpected transcription type: {type(transcription)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ElevenLabs STT error: {str(e)}")