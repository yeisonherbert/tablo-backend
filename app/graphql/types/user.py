import uuid
from datetime import datetime

import strawberry

from app.models import User


@strawberry.type(name="User")
class UserType:
    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None
    created_at: datetime

    @classmethod
    def from_model(cls, user: User) -> "UserType":
        return cls(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
        )
