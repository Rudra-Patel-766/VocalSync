import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "mysql+mysqlconnector://root:vyom%402004@localhost:3306/speech_coach"
    
    # Firebase
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY_ID: Optional[str] = None
    FIREBASE_PRIVATE_KEY: Optional[str] = None
    FIREBASE_CLIENT_EMAIL: Optional[str] = None
    FIREBASE_CLIENT_ID: Optional[str] = None
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Speech Coach"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    CORS_ORIGIN_REGEX: Optional[str] = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Audio Processing
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHUNK_SIZE: int = 1024
    MAX_AUDIO_SIZE: int = 25 * 1024 * 1024  # 25MB
    
    # AI Models
    WHISPER_MODEL: str = "base"
    GROQ_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def cors_origins_list(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
