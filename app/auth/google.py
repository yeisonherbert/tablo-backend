from dataclasses import dataclass

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import settings


@dataclass(frozen=True)
class GoogleUserInfo:
    google_id: str
    email: str
    name: str
    avatar_url: str | None


def verify_google_token(token: str) -> GoogleUserInfo:
    """Verifica un id_token de Google y devuelve los datos básicos del usuario.

    En entornos donde GOOGLE_CLIENT_ID está vacío (desarrollo local), no se
    valida la audiencia — pero la firma y el emisor sí se siguen verificando
    contra los servidores de Google.
    """
    audience = settings.GOOGLE_CLIENT_ID or None
    try:
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), audience
        )
    except ValueError as exc:
        raise ValueError(f"Token de Google inválido: {exc}") from exc

    return GoogleUserInfo(
        google_id=idinfo["sub"],
        email=idinfo["email"],
        name=idinfo.get("name") or idinfo["email"],
        avatar_url=idinfo.get("picture"),
    )
