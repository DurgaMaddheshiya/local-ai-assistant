"""
Configuration management for Local AI Assistant
"""
import os
import logging
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Ollama Configuration
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout: int = 120
    
    # Database
    database_path: str = "./data/app.db"
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Security
    secret_key: str = "local-ai-assistant-secret-key-change-in-production"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    # AI Settings
    default_temperature: float = 0.7
    default_max_tokens: int = 2048
    default_context_length: int = 4096
    
    # System
    app_name: str = "Local AI Assistant"
    app_version: str = "1.0.0"
    
    # Default system prompt
    default_system_prompt: str = (
        "You are a helpful local AI assistant running on the user's computer. "
        "You do not have internet access unless the user explicitly enables an external feature. "
        "Be honest about your capabilities. Give clear, useful and accurate answers. "
        "Never claim to have accessed information that you did not access."
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()


def setup_logging(settings: Settings) -> None:
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )


def ensure_directories(settings: Settings) -> None:
    """Ensure required directories exist"""
    directories = [
        Path(settings.database_path).parent,
        Path(settings.log_file).parent,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = get_settings()