from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
import os
from typing import Optional

DOTENV = os.path.join(os.path.dirname(__file__), ".env")
class Settings(BaseSettings):
    # Database Configuration
    database_hostname: str 
    database_password: str 
    database_name:str
    database_username:str
    database_port:str
    jwt_secret:str
    jwt_algorithm:str
    redis_host:str
    redis_port:str
    redis_password:str
    google_client_id:str
    google_client_secret:str
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_from_name: str

    # Groq API Configuration
    groq_api_key: str
    upstash_redis_rest_url: str
    upstash_redis_rest_token: str

    gemini_api_key:str


  
    class Config:
        env_file = DOTENV  
        env_file_encoding = 'utf-8'
        
    
settings=Settings()