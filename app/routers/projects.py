"""Router de proyectos: crear, listar, detalle, añadir miembros y crear tareas."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.project import Project, project_members
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.project import (
    AddMemberRequest,
    ProjectCreate,
    ProjectDetailOut,
    ProjectOut,
)
from app.schemas.task import TaskCreate, TaskOut

router = APIRouter(prefix="/projects", tags=["projects"])


async def _get_project_or_403(
    project_id: uuid.UUID, user: User, db: AsyncSession
) -> Project:
    """Devuelve el proyecto si el usuario es dueño o participante; si no, 404/403."""
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado"
        )
    member_ids = {m.id for m in project.members}
    if user.id != project.owner_id and user.id not in member_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este proyecto",
        )
    return project


@router.post(
    "",
    response_model=ProjectDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un proyecto",
)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Project:
    project = Project(
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
    )
    # El dueño también queda como participante del proyecto.
    project.members.append(current_user)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get(
    "",
    response_model=list[ProjectOut],
    summary="Listar los proyectos del usuario logueado (propios y como miembro)",
)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    stmt = (
        select(Project)
        .where(
            or_(
                Project.owner_id == current_user.id,
                Project.members.any(User.id == current_user.id),
            )
        )
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


@router.get(
    "/{project_id}",
    response_model=ProjectDetailOut,
    summary="Detalle del proyecto con participantes y tareas ordenadas por estado",
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectDetailOut:
    project = await _get_project_or_403(project_id, current_user, db)

    # Tareas ordenadas por estado (flujo Kanban) y luego por posición.
    tasks_stmt = (
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.status, Task.position, Task.created_at)
    )
    tasks = list((await db.execute(tasks_stmt)).scalars().all())

    return ProjectDetailOut(
        id=project.id,
        owner_id=project.owner_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        owner=project.owner,
        members=project.members,
        tasks=tasks,
    )


@router.post(
    "/{project_id}/members",
    response_model=ProjectDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir un participante al proyecto (por email)",
)
async def add_member(
    project_id: uuid.UUID,
    payload: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectDetailOut:
    project = await _get_project_or_403(project_id, current_user, db)

    result = await db.execute(select(User).where(User.email == payload.email))
    new_member = result.scalar_one_or_none()
    if new_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe un usuario con ese correo",
        )

    if new_member.id not in {m.id for m in project.members}:
        project.members.append(new_member)
        await db.commit()
        await db.refresh(project)

    return await get_project(project_id, current_user, db)


@router.post(
    "/{project_id}/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una tarea (nace en 'backlog')",
)
async def create_task(
    project_id: uuid.UUID,
    payload: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    project = await _get_project_or_403(project_id, current_user, db)

    # Validamos que el responsable (si se indica) sea participante del proyecto.
    if payload.assignee_id is not None:
        valid_ids = {project.owner_id} | {m.id for m in project.members}
        if payload.assignee_id not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El responsable debe ser participante del proyecto",
            )

    # La nueva tarjeta se ubica al final de la columna 'backlog'.
    max_pos = (
        await db.execute(
            select(func.coalesce(func.max(Task.position), 0)).where(
                Task.project_id == project_id,
                Task.status == TaskStatus.backlog,
            )
        )
    ).scalar_one()

    task = Task(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        status=TaskStatus.backlog,
        assignee_id=payload.assignee_id,
        position=float(max_pos) + 1,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task
