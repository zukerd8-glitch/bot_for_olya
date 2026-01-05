import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Telegram Bot Token
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    # Bot settings
    BOT_ADMIN_ID: Optional[int] = os.getenv("BOT_ADMIN_ID")
    CONTEXT_MEMORY_SIZE: int = int(os.getenv("CONTEXT_MEMORY_SIZE", "10"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./olya_bot.db")
    
    # Fallback settings
    USE_FALLBACK_MODEL: bool = os.getenv("USE_FALLBACK_MODEL", "False").lower() == "true"
    FALLBACK_MODEL_PATH: Optional[str] = os.getenv("FALLBACK_MODEL_PATH")
    
    class Config:
        env_file = ".env"

settings = Settings()
