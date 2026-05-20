"""Esquemas Pydantic del Proyecto."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.task import TaskOut
from app.schemas.user import UserOut


class ProjectCreate(BaseModel):
    """Cuerpo para crear un proyecto."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class AddMemberRequest(BaseModel):
    """Cuerpo para añadir un participante por correo."""

    email: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("Correo inválido")
        return normalized


class ProjectOut(BaseModel):
    """Representación resumida de un proyecto (para el listado)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectDetailOut(ProjectOut):
    """Proyecto con sus participantes y tareas (ordenadas por estado)."""

    owner: UserOut
    members: list[UserOut] = []
    tasks: list[TaskOut] = []
