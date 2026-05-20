"""Modelo ORM de Proyecto (tabla `projects`) y tabla pivote `project_members`."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User

# Tabla pivote N:M entre proyectos y usuarios participantes.
project_members = Table(
    "project_members",
    Base.metadata,
    Column(
        "project_id",
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("joined_at", DateTime(timezone=True), server_default=func.now()),
)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relaciones (carga selectin para que funcionen en contexto async).
    owner: Mapped[User] = relationship("User", lazy="selectin")
    members: Mapped[list[User]] = relationship(
        "User",
        secondary=project_members,
        lazy="selectin",
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Task.position",
    )
