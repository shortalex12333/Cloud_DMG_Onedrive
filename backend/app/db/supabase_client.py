"""Supabase client for database operations via REST API"""
from supabase import create_client, Client
from app.config import settings
from typing import Optional

# Global Supabase client
_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """Get or create Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    return _supabase_client


def get_supabase_dependency():
    """FastAPI dependency for Supabase client"""
    return get_supabase()
