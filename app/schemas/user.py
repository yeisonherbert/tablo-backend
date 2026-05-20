"""Esquemas Pydantic del Usuario."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserOut(BaseModel):
    """Representación pública de un usuario."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    name: str
    avatar_url: str | None = None
    created_at: datetime
    updated_at: datetime
