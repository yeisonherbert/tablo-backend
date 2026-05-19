import uuid
from datetime import datetime
from typing import List

import strawberry
from sqlalchemy import case, select
from sqlalchemy.orm import selectinload
from strawberry.types import Info

from app.graphql.types.task import TaskType
from app.graphql.types.user import UserType
from app.models import Project, Task, TaskStatus


# Orden canónico de las columnas Kanban: backlog → to_do → in_progress → completed
_STATUS_ORDER = case(
    {
        TaskStatus.BACKLOG: 0,
        TaskStatus.TO_DO: 1,
        TaskStatus.IN_PROGRESS: 2,
        TaskStatus.COMPLETED: 3,
    },
    value=Task.status,
)


@strawberry.type(name="Project")
class ProjectType:
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, project: Project) -> "ProjectType":
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            owner_id=project.owner_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @strawberry.field
    async def tasks(self, info: Info) -> List[TaskType]:
        session = info.context.session
        result = await session.execute(
            select(Task)
            .where(Task.project_id == self.id)
            .order_by(_STATUS_ORDER, Task.created_at)
        )
        return [TaskType.from_model(t) for t in result.scalars().all()]

    @strawberry.field
    async def owner(self, info: Info) -> UserType:
        from app.models import User  # evita ciclo

        session = info.context.session
        user = await session.get(User, self.owner_id)
        return UserType.from_model(user)  # type: ignore[arg-type]

    @strawberry.field
    async def collaborators(self, info: Info) -> List[UserType]:
        session = info.context.session
        result = await session.execute(
            select(Project)
            .where(Project.id == self.id)
            .options(selectinload(Project.collaborators))
        )
        project = result.scalar_one()
        return [UserType.from_model(u) for u in project.collaborators]
