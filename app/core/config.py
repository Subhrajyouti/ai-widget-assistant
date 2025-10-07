from pydantic import BaseSettings
from typing import Optional




class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL: int = 3600 # seconds
    USE_MOCK_LLM: bool = True
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_SECRET_NAME: Optional[str] = "gemini/keys"
    AWS_REGION: str = "us-east-1"
    APP_PORT: int = 8080


class Config:
 env_file = ".env"




settings = Settings()