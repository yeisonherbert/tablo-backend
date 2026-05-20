"""Esquemas Pydantic de la Tarea."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus
from app.schemas.user import UserOut


class TaskCreate(BaseModel):
    """Cuerpo para crear una tarea. Siempre nace en 'backlog'."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    assignee_id: uuid.UUID | None = None


class TaskStatusUpdate(BaseModel):
    """Cuerpo para mover una tarjeta entre columnas del tablero."""

    status: TaskStatus
    position: float | None = None


class TaskOut(BaseModel):
    """Representación de una tarea para el cliente."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None = None
    status: TaskStatus
    assignee_id: uuid.UUID | None = None
    assignee: UserOut | None = None
    position: float | None = None
    created_at: datetime
    updated_at: datetime
