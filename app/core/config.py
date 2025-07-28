from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # Application Info
    app_name: str = "DogTorVet API"
    app_version: str = "2.0.0"
    description: str = "Veterinary Management System API"
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    environment: str = "development"
    
    # Database Settings - Use MongoDB Atlas by default
    database_url: str = "mongodb+srv://dogtorvetservices:6MotTn1RO4O764IL@dogtorvetdata.re8rk.mongodb.net/dogtorvet"
    database_name: str = "dogtorvet"
    mongodb_url: Optional[str] = None  # Support for both naming conventions
    
    # Security Settings
    secret_key: str = "your-secret-key-here-change-in-production-2025-dogtorvet"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 240
    refresh_token_expire_days: int = 7
    
    # CORS Settings
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://dogtorvetservices.onrender.com",
        "https://dogtorvet-ui.onrender.com"
    ]
    
    # Admin User Settings
    admin_email: str = "admin@dogtorvet.com"
    admin_password: str = "Dogtorvet@2025"
    admin_first_name: str = "System"
    admin_last_name: str = "Administrator"
    
    # Support for legacy environment variable names
    root_user_email: Optional[str] = None
    root_user_password: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from environment
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Handle legacy environment variable names
        if self.mongodb_url and not kwargs.get('database_url'):
            self.database_url = self.mongodb_url
        
        if self.root_user_email and not kwargs.get('admin_email'):
            self.admin_email = self.root_user_email
        
        if self.root_user_password and not kwargs.get('admin_password'):
            self.admin_password = self.root_user_password


# Create global settings instance
settings = Settings() 