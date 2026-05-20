"""Dependencias de FastAPI para proteger los endpoints con JWT."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import JWTError, decode_access_token
from app.database import get_db
from app.models.user import User

# `auto_error=True` => responde 403 automáticamente si falta el header.
bearer_scheme = HTTPBearer(description="JWT emitido por POST /auth/login")

_credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas o token expirado",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Valida el JWT del header `Authorization: Bearer <token>` y devuelve el usuario."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise _credentials_exc
        user_id = uuid.UUID(subject)
    except (JWTError, ValueError):
        raise _credentials_exc

    user = await db.get(User, user_id)
    if user is None:
        raise _credentials_exc
    return user
