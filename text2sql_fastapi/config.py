from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os

"""
Configuration module for environment variables and application settings using Pydantic.
Loads .env file and provides a Settings class for global config access.
"""

# ✅ Load .env manually before instantiating the Settings
DOTENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(DOTENV_PATH)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables using Pydantic BaseSettings.
    """
    # Database Configuration
    database_hostname: str 
    database_password: str 
    database_name: str
    database_username: str
    database_port: str

    # JWT Configuration
    jwt_secret: str
    jwt_algorithm: str

    # Redis Configuration
    redis_host: str
    redis_port: str
    redis_password: str

    # Google OAuth Configuration
    google_client_id: str
    google_client_secret: str

    # Mail Configuration
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_from_name: str

    # API Keys and Services
    groq_api_key: str
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str
    gemini_api_key: str
    elevenlabs_api_key: str

    # Defaults (optional)
    default_voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    default_model_id: str = "eleven_flash_v2_5"
    default_output_format: str = "mp3_44100_128"

    model_config = SettingsConfigDict(env_file=DOTENV_PATH, extra="allow")

# Instantiate the settings
settings = Settings()