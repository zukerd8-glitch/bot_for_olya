import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Telegram Bot Token (обязательный)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # OpenRouter (ваш ключ)
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
    
    # Database (особый путь для Render)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./olya_bot.db")
    
    # Если на Render, используем персистентный диск
    if "RENDER" in os.environ:
        DATABASE_URL = "sqlite:///./data/olya_bot.db"
    
    # Bot settings
    BOT_ADMIN_ID: Optional[int] = os.getenv("BOT_ADMIN_ID")
    CONTEXT_MEMORY_SIZE: int = int(os.getenv("CONTEXT_MEMORY_SIZE", "10"))
    
    # Приоритет провайдеров для Render
    AI_PROVIDER_PRIORITY: List[str] = os.getenv(
        "AI_PROVIDER_PRIORITY", 
        "openrouter,fallback"
    ).split(",")
    
    class Config:
        env_file = ".env"

settings = Settings()
