from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.google import verify_google_token
from app.auth.jwt_handler import create_access_token
from app.database import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleLoginInput(BaseModel):
    id_token: str = Field(..., description="id_token obtenido del cliente Google")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/google", response_model=TokenResponse)
async def login_with_google(
    payload: GoogleLoginInput,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    try:
        info = verify_google_token(payload.id_token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    result = await session.execute(
        select(User).where(User.google_id == info.google_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            google_id=info.google_id,
            email=info.email,
            name=info.name,
            avatar_url=info.avatar_url,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))
