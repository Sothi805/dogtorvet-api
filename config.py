from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database Configuration
    mongodb_url: str = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")
    database_name: str = os.environ.get("DATABASE_NAME", "dogtorvet")
    
    # JWT Configuration
    secret_key: str = os.environ.get("SECRET_KEY", "development-secret-key-CHANGE-IN-PRODUCTION")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "240"))  # 4 hours
    refresh_token_expire_days: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Application Configuration
    app_name: str = "DogTorVet API"
    app_version: str = "1.0.0"
    debug: bool = os.environ.get("DEBUG", "False").lower() == "true"
    environment: str = os.environ.get("ENVIRONMENT", "development")
    
    # CORS Configuration - will be overridden in main.py but kept for reference
    allowed_origins: List[str] = [
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://dogtorvet-ui.onrender.com",
        "https://dogtorvetservices.onrender.com"
    ]
    
    # Security
    bcrypt_rounds: int = 12
    
    # Root User Configuration (for seeding)
    root_user_email: str = os.environ.get("ROOT_USER_EMAIL", "admin@dogtorvet.com")
    root_user_password: str = os.environ.get("ROOT_USER_PASSWORD", "ChangeMeInProduction123!")
    root_user_first_name: str = "System"
    root_user_last_name: str = "Administrator"
    root_user_phone: str = "+1234567890"
    root_user_specialization: str = "System Administration"
    
    # File Upload Configuration
    max_file_size: int = 5242880  # 5MB in bytes
    upload_folder: str = "uploads"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = int(os.environ.get("PORT", "8000"))
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 