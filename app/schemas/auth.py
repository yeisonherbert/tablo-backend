"""Esquemas Pydantic de autenticación."""
from pydantic import BaseModel, field_validator

from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    """Cuerpo del login: solo el correo (debe ser @gmail.com)."""

    email: str

    @field_validator("email")
    @classmethod
    def must_be_gmail(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("El correo es obligatorio")
        if "@" not in normalized or not normalized.endswith("@gmail.com"):
            raise ValueError("Solo se permiten correos @gmail.com")
        local_part = normalized.split("@", 1)[0]
        if not local_part:
            raise ValueError("Correo inválido")
        return normalized


class TokenResponse(BaseModel):
    """Respuesta del login: el JWT y el usuario autenticado."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut
