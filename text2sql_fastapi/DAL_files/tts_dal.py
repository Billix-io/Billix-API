import os
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from schemas.tts_schemas import TTSRequest
from fastapi import HTTPException
from config import settings




# Use environment variable for API key and TTS defaults from settings
ELEVENLABS_API_KEY = settings.elevenlabs_api_key
DEFAULT_VOICE_ID = settings.default_voice_id
DEFAULT_MODEL_ID = settings.default_model_id
DEFAULT_OUTPUT_FORMAT = settings.default_output_format

class TTSDAL:
    async def text_to_speech(self, tts_request: TTSRequest) -> bytes:
        # Use ElevenLabs SDK (sync, so run in threadpool)
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._sync_text_to_speech, tts_request)

    def _sync_text_to_speech(self, tts_request: TTSRequest) -> bytes:
        client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        text_input = tts_request.text
        voice_id = settings.default_voice_id
        model_id = settings.default_model_id
        output_format = settings.default_output_format
        # Optional: tune voice settings
        voice_settings = VoiceSettings(
            stability=0.5,
            similarity_boost=0.75
        )
        try:
            audio_stream = client.text_to_speech.convert(
                text=text_input,
                voice_id=voice_id,
                model_id=model_id,
                optimize_streaming_latency="0",
                voice_settings=voice_settings,
                output_format=output_format
            )
            audio_bytes = b""
            for chunk in audio_stream:
                if chunk:
                    audio_bytes += chunk
            return audio_bytes
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ElevenLabs TTS error: {str(e)}") 