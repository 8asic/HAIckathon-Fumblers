import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY")
    newsapi_ai_key: str = os.getenv("NEWSAPI_AI_KEY")
    newsapi_key: str = os.getenv("NEWS_API_KEY")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY")  # For future voice
    
    # Application Settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # News API Settings
    default_query: str = "climate change"
    max_articles: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()