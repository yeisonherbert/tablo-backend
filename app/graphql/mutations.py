import uuid

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from strawberry.types import Info

from app.graphql.permissions import IsAuthenticated
from app.graphql.types import ProjectType, TaskType
from app.graphql.types.task import TaskStatusEnum
from app.models import Project, Task, TaskStatus, User


async def _load_project_for_member(
    session, project_id: uuid.UUID, user: User
) -> Project | None:
    """Devuelve el proyecto si el usuario es dueño o colaborador, si no None."""
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.collaborators))
    )
    result = await session.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        return None
    if project.owner_id == user.id:
        return project
    if any(c.id == user.id for c in project.collaborators):
        return project
    return None


@strawberry.type
class Mutation:
    # ---------------------------- Proyectos -----------------------------

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_project(
        self, info: Info, name: str, description: str | None = None
    ) -> ProjectType:
        session = info.context.session
        current = info.context.user

        project = Project(name=name, description=description, owner_id=current.id)
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return ProjectType.from_model(project)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def add_collaborator(
        self, info: Info, project_id: uuid.UUID, email: str
    ) -> ProjectType:
        session = info.context.session
        current = info.context.user

        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.collaborators))
        )
        project = (await session.execute(stmt)).scalar_one_or_none()
        if project is None:
            raise ValueError("Proyecto no encontrado")
        if project.owner_id != current.id:
            raise ValueError("Sólo el dueño puede añadir colaboradores")

        user_to_add = (
            await session.execute(select(User).where(User.email == email))
        ).scalar_one_or_none()
        if user_to_add is None:
            raise ValueError(f"No existe usuario con email {email}")

        if user_to_add.id == project.owner_id:
            raise ValueError("El dueño ya tiene acceso al proyecto")

        if any(c.id == user_to_add.id for c in project.collaborators):
            return ProjectType.from_model(project)

        project.collaborators.append(user_to_add)
        await session.commit()
        await session.refresh(project)
        return ProjectType.from_model(project)

    # ----------------------------- Tareas -------------------------------

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_task(
        self,
        info: Info,
        project_id: uuid.UUID,
        title: str,
        description: str | None = None,
        assignee_id: uuid.UUID | None = None,
    ) -> TaskType:
        session = info.context.session
        current = info.context.user

        project = await _load_project_for_member(session, project_id, current)
        if project is None:
            raise ValueError("Proyecto no encontrado o sin acceso")

        task = Task(
            project_id=project_id,
            title=title,
            description=description,
            status=TaskStatus.BACKLOG,
            assignee_id=assignee_id,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return TaskType.from_model(task)

    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def move_task(
        self,
        info: Info,
        task_id: uuid.UUID,
        new_status: TaskStatusEnum,  # type: ignore[valid-type]
    ) -> TaskType:
        """Mueve una tarea entre columnas del Kanban
        ('backlog' | 'to_do' | 'in_progress' | 'completed')."""
        session = info.context.session
        current = info.context.user

        task = await session.get(Task, task_id)
        if task is None:
            raise ValueError("Tarea no encontrada")

        project = await _load_project_for_member(session, task.project_id, current)
        if project is None:
            raise ValueError("Sin acceso a esta tarea")

        task.status = new_status  # type: ignore[assignment]
        await session.commit()
        await session.refresh(task)
        return TaskType.from_model(task)
