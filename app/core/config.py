from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    APP_NAME: str = "Conversational Assessment Recommender"
    ENV: str = "development"
    PORT: int = 8000
    
    GEMINI_API_KEY: Optional[str] = None
    VECTOR_DB_DIR: str = "./data/vector_db"
    CATALOG_URL: str = "https://www.shl.com/solutions/products/product-catalog/"

settings = Settings()
