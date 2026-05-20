"""Modelo ORM de Tarea (tabla `tasks`) y el ENUM `task_status`."""
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User


class TaskStatus(str, enum.Enum):
    """Estados posibles de una tarjeta del tablero Kanban.

    El orden de declaración coincide con el ENUM de PostgreSQL, por lo que
    `ORDER BY status` respeta este flujo de izquierda a derecha.
    """

    backlog = "backlog"
    to_do = "to_do"
    in_progress = "in_progress"
    completed = "completed"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        # El tipo ya existe en la BD: no intentamos crearlo de nuevo.
        SAEnum(
            TaskStatus,
            name="task_status",
            create_type=False,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=TaskStatus.backlog,
        server_default="backlog",
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    position: Mapped[Decimal] = mapped_column(
        Numeric, nullable=True, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="tasks"
    )
    assignee: Mapped[User | None] = relationship("User", lazy="selectin")
