# src/core/config.py

from typing import Dict, Optional
from pydantic import BaseSettings
import logging
import sys
from pathlib import Path

class Settings(BaseSettings):
    # Azure Settings
    AZURE_CLIENT_ID: str
    AZURE_CLIENT_SECRET: str
    AZURE_TENANT_ID: str
    
    # OpenAI Settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    
    # Application Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Redis Settings
    REDIS_URL: str = "redis://redis:6379/0"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Agents Platform"
    
    class Config:
        case_sensitive = True

def setup_logging(settings: Settings) -> None:
    """Configure logging for the application"""
    log_level = getattr(logging, settings.LOG_LEVEL.upper())
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path(__file__).parent.parent.parent / "logs" / "app.log"
            )
        ]
    )
    
    # Set lower log levels for some chatty libraries
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

settings = Settings()
setup_logging(settings)