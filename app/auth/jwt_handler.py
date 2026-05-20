"""Generación y validación de JSON Web Tokens propios del sistema."""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings


def create_access_token(subject: str) -> str:
    """Firma un JWT cuyo `sub` es el id (UUID) del usuario."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza JWTError si es inválido o expiró."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


__all__ = ["create_access_token", "decode_access_token", "JWTError"]
