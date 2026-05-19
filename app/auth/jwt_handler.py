import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.config import settings


class InvalidTokenError(Exception):
    """Se lanza cuando un JWT es inválido, está expirado o malformado."""


def create_access_token(
    user_id: uuid.UUID, extra_claims: dict[str, Any] | None = None
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc


def extract_user_id(token: str) -> uuid.UUID:
    payload = decode_access_token(token)
    sub = payload.get("sub")
    if not sub:
        raise InvalidTokenError("Token sin claim 'sub'")
    try:
        return uuid.UUID(sub)
    except ValueError as exc:
        raise InvalidTokenError("Claim 'sub' no es un UUID válido") from exc
