"""
Симметричное шифрование токенов (Fernet = AES-128-CBC + HMAC-SHA256).
Ключ берётся из SECRET_KEY приложения — при ротации ключа нужен ре-энкрипт.
"""
import base64
import hashlib

from cryptography.fernet import Fernet

from app.config import settings

# Fernet требует 32 байта base64url. Деривируем из SECRET_KEY через SHA-256.
def _fernet() -> Fernet:
    key_bytes = hashlib.sha256(settings.secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_token(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()
