"""Router de autenticación simulada (Email + JWT, sin contraseñas)."""
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_handler import create_access_token
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _name_from_email(email: str) -> str:
    """Genera un nombre legible a partir del correo. p.ej. john.doe -> John Doe."""
    local_part = email.split("@", 1)[0]
    words = local_part.replace(".", " ").replace("_", " ").replace("-", " ").split()
    return " ".join(w.capitalize() for w in words) or local_part


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login simulado: recibe un correo @gmail.com y devuelve un JWT",
)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    email = payload.email

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Si el usuario no existe, lo creamos al vuelo (sin contraseña).
    if user is None:
        user = User(
            email=email,
            name=_name_from_email(email),
            avatar_url=settings.AVATAR_BASE_URL,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token, user=user)
