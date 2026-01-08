"""Token encryption utilities using Fernet symmetric encryption"""
import base64
from typing import Optional
from cryptography.fernet import Fernet
from app.config import settings


class TokenEncryption:
    """Handles encryption and decryption of OAuth tokens"""

    def __init__(self):
        """Initialize with encryption key from settings"""
        if not settings.token_encryption_key:
            raise ValueError("TOKEN_ENCRYPTION_KEY not configured")

        # Ensure key is valid Fernet key
        try:
            self.fernet = Fernet(settings.token_encryption_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid TOKEN_ENCRYPTION_KEY: {e}")

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a token string

        Args:
            token: Plain text token to encrypt

        Returns:
            Base64-encoded encrypted token
        """
        if not token:
            raise ValueError("Token cannot be empty")

        encrypted = self.fernet.encrypt(token.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt an encrypted token

        Args:
            encrypted_token: Base64-encoded encrypted token

        Returns:
            Plain text token
        """
        if not encrypted_token:
            raise ValueError("Encrypted token cannot be empty")

        try:
            decoded = base64.b64decode(encrypted_token.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt token: {e}")

    def validate_token(self, encrypted_token: str) -> bool:
        """
        Validate that a token can be decrypted

        Args:
            encrypted_token: Base64-encoded encrypted token

        Returns:
            True if valid, False otherwise
        """
        try:
            self.decrypt_token(encrypted_token)
            return True
        except Exception:
            return False


# Global instance
_encryption = None

def get_encryption() -> TokenEncryption:
    """Get global encryption instance"""
    global _encryption
    if _encryption is None:
        _encryption = TokenEncryption()
    return _encryption
