"""Application configuration"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Azure AD Configuration
    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    azure_client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")
    azure_redirect_uri: str = os.getenv("AZURE_REDIRECT_URI", "http://localhost:3000/api/v1/auth/callback")

    # Azure AD OAuth Scopes
    azure_scopes: list = ["Files.Read.All", "User.Read", "offline_access"]

    # Token Encryption
    token_encryption_key: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")

    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "https://vzsohavtuotocgrfkfyd.supabase.co")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")

    # Document Processing
    digest_service_url: str = os.getenv("DIGEST_SERVICE_URL", "https://celeste-digest-index.onrender.com")
    yacht_salt: str = os.getenv("YACHT_SALT", "e49469e09cb6529e0bfef118370cf8425b006f0abbc77475da2e0cb479af8b18")

    # Backend Configuration
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")

    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS Origins (for frontend)
    cors_origins: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
