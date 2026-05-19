from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from app.auth.dependencies import get_optional_user
from app.database import get_session
from app.models import User


@dataclass
class Context(BaseContext):
    session: AsyncSession
    user: User | None = None


async def get_context(
    session: AsyncSession = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> Context:
    return Context(session=session, user=user)
