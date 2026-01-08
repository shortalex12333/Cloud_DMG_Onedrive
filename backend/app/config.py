"""Application configuration"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Azure AD Configuration
    azure_tenant_id: str = os.getenv("AZURE_TENANT_ID", "")
    azure_client_id: str = os.getenv("AZURE_CLIENT_ID", "")
    azure_client_secret: str = os.getenv("AZURE_CLIENT_SECRET", "")

    @property
    def azure_redirect_uri(self) -> str:
        """Return Azure redirect URI based on environment"""
        # Always use BACKEND URL on Render (callback endpoint is on backend!)
        if os.getenv("RENDER"):
            return "https://digest-cloud.int.celeste7.ai/api/v1/auth/callback"
        # Otherwise use env var or localhost default
        return os.getenv("AZURE_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback")

    @property
    def azure_scopes(self) -> list:
        """Return Azure AD OAuth scopes as a fresh list

        Using .default scope for confidential client app.
        This requests all permissions granted to the app registration.
        """
        return ["https://graph.microsoft.com/.default"]

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
    @property
    def cors_origins(self) -> List[str]:
        """Return CORS origins from environment or defaults"""
        env_origins = os.getenv("CORS_ORIGINS", "")
        if env_origins:
            origins = [origin.strip() for origin in env_origins.split(",")]
        else:
            origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]

        # Always include production URLs
        production_urls = [
            "https://celesteos-onedrive-portal.onrender.com",
            "https://digest.celeste7.ai",  # Production frontend
            "https://cloud.celeste7.ai"
        ]

        for url in production_urls:
            if url not in origins:
                origins.append(url)

        return origins

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
