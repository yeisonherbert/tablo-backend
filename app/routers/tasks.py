"""Router de tareas: actualizar el estado (mover entre columnas del tablero)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskOut, TaskStatusUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def _get_task_for_user(
    task_id: uuid.UUID, user: User, db: AsyncSession
) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada"
        )
    project = await db.get(Project, task.project_id)
    member_ids = {m.id for m in project.members}
    if user.id != project.owner_id and user.id not in member_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta tarea",
        )
    return task


@router.patch(
    "/{task_id}",
    response_model=TaskOut,
    summary="Actualizar el estado de una tarea (backlog/to_do/in_progress/completed)",
)
async def update_task_status(
    task_id: uuid.UUID,
    payload: TaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    task = await _get_task_for_user(task_id, current_user, db)

    task.status = payload.status
    if payload.position is not None:
        task.position = payload.position

    await db.commit()
    await db.refresh(task)
    return task
