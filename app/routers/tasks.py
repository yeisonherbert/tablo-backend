"""Router de tareas: actualizar el estado (mover entre columnas del tablero)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskOut, TaskStatusUpdate, TaskUpdate

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


@router.put(
    "/{task_id}/details",
    response_model=TaskOut,
    summary="Actualizar los detalles generales de una tarea",
)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Task:
    task = await _get_task_for_user(task_id, current_user, db)

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    
    # We update the assignee_id since it might be set to None or a new UUID
    # Although pydantic model separates unset and None, it's easier to use model_dump(exclude_unset=True)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una tarea",
)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await _get_task_for_user(task_id, current_user, db)
    await db.delete(task)
    await db.commit()

