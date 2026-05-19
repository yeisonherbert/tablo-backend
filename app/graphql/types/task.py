import uuid
from datetime import datetime

import strawberry

from app.models import Task, TaskStatus

TaskStatusEnum = strawberry.enum(TaskStatus, name="TaskStatus")


@strawberry.type(name="Task")
class TaskType:
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatusEnum  # type: ignore[valid-type]
    assignee_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, task: Task) -> "TaskType":
        return cls(
            id=task.id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            status=task.status,
            assignee_id=task.assignee_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
