import uuid
from typing import List

import strawberry
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from strawberry.types import Info

from app.graphql.permissions import IsAuthenticated
from app.graphql.types import ProjectType, UserType
from app.models import Project


@strawberry.type
class Query:
    @strawberry.field(permission_classes=[IsAuthenticated])
    async def me(self, info: Info) -> UserType:
        return UserType.from_model(info.context.user)

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def my_projects(self, info: Info) -> List[ProjectType]:
        """Proyectos donde el usuario es dueño o colaborador."""
        session = info.context.session
        current = info.context.user

        stmt = (
            select(Project)
            .outerjoin(Project.collaborators)
            .where(
                or_(
                    Project.owner_id == current.id,
                    Project.collaborators.any(id=current.id),
                )
            )
            .distinct()
            .order_by(Project.created_at.desc())
        )
        result = await session.execute(stmt)
        return [ProjectType.from_model(p) for p in result.scalars().unique().all()]

    @strawberry.field(permission_classes=[IsAuthenticated])
    async def project(self, info: Info, project_id: uuid.UUID) -> ProjectType | None:
        """Carga un proyecto sólo si el usuario tiene acceso (dueño o colaborador)."""
        session = info.context.session
        current = info.context.user

        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.collaborators))
        )
        result = await session.execute(stmt)
        project = result.scalar_one_or_none()
        if project is None:
            return None

        is_owner = project.owner_id == current.id
        is_collaborator = any(c.id == current.id for c in project.collaborators)
        if not (is_owner or is_collaborator):
            return None

        return ProjectType.from_model(project)
