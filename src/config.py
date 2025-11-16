"""
NovaPorra - MotoGP Betting System
Configuration management
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "NovaPorra"
    app_timezone: str = "Europe/Madrid"
    bet_close_minutes: int = 10
    current_season: int = 2024
    debug: bool = False
    
    # Telegram Bot
    telegram_bot_token: str
    
    # MySQL Database
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "novaporra"
    mysql_user: str
    mysql_password: str
    mysql_root_password: Optional[str] = None
    
    # MotoGP API
    motogp_api_url: str = "https://api.motogp.com/"
    motogp_api_key: Optional[str] = None
    motogp_api_secret: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/novaporra.log"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def database_url(self) -> str:
        """Get MySQL connection URL"""
        return (
            f"mysql+mysqlconnector://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


# Global settings instance
settings = Settings()
