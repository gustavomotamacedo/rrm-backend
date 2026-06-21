import logging
import uuid
import hashlib
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, RequiresResident
from app.db.session import get_db
from app.models.user import User
from app.models.residence import Resident
from app.models.task import Recurrence, Task, TaskExecution, TaskStatus
from app.models.attachment import Attachment
from app.services.storage import BaseStorageService, get_storage_service
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskExecutionCreate,
    TaskExecutionResponse,
    AttachmentResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/residences/{residence_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(
    residence_id: uuid.UUID,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all tasks for a specific residence. Requires active membership."""
    stmt = select(Task).where(
        Task.residence_id == residence_id,
        Task.deleted_at.is_(None)
    ).options(
        selectinload(Task.recurrence),
        selectinload(Task.attachments)
    )
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return tasks


@router.post("/residences/{residence_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    residence_id: uuid.UUID,
    task_in: TaskCreate,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Creates a new task in the residence.

    If recurrence parameters are provided, creates the recurrence rule first.
    """
    # 1. Verify assigned resident belongs to same residence (if provided)
    if task_in.assigned_resident_id:
        stmt = select(Resident).where(
            Resident.id == task_in.assigned_resident_id,
            Resident.residence_id == residence_id,
            Resident.left_at.is_(None)
        )
        result = await db.execute(stmt)
        assigned = result.scalar_one_or_none()
        if not assigned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned resident must be an active member of this residence."
            )

    # 2. Create Recurrence rule if provided
    recurrence = None
    if task_in.recurrence:
        recurrence = Recurrence(
            frequency=task_in.recurrence.frequency,
            interval_value=task_in.recurrence.interval_value,
            by_week_day=task_in.recurrence.by_week_day,
            by_month_day=task_in.recurrence.by_month_day,
            start_date=task_in.recurrence.start_date,
            end_date=task_in.recurrence.end_date
        )
        db.add(recurrence)
        await db.flush()

    # 3. Create Task
    new_task = Task(
        residence_id=residence_id,
        assigned_resident_id=task_in.assigned_resident_id,
        recurrence_id=recurrence.id if recurrence else None,
        title=task_in.title,
        description=task_in.description,
        status=TaskStatus.PENDING,
        due_at=task_in.due_at
    )
    db.add(new_task)
    await db.commit()

    # Reload relationships for response serialization
    stmt_reload = select(Task).where(Task.id == new_task.id).options(
        selectinload(Task.recurrence),
        selectinload(Task.attachments)
    )
    result_reload = await db.execute(stmt_reload)
    task_response = result_reload.scalar_one()

    logger.info(f"Task {new_task.id} created by resident {active_resident.id}.")
    return task_response


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Gets details of a task. Caller must belong to the task's residence."""
    stmt = select(Task).where(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).options(
        selectinload(Task.recurrence),
        selectinload(Task.attachments)
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Verify membership
    stmt_member = select(Resident).where(
        Resident.residence_id == task.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this task."
        )

    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates task properties.

    - Caller must belong to the task's residence.
    - If status changes to COMPLETED, completed_at is automatically logged.
    - If status is changed back, completed_at is cleared.
    """
    stmt = select(Task).where(
        Task.id == task_id,
        Task.deleted_at.is_(None)
    ).options(
        selectinload(Task.recurrence),
        selectinload(Task.attachments)
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == task.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this task."
        )

    # Verify assigned resident (if provided)
    if task_in.assigned_resident_id:
        stmt_assignee = select(Resident).where(
            Resident.id == task_in.assigned_resident_id,
            Resident.residence_id == task.residence_id,
            Resident.left_at.is_(None)
        )
        result_assignee = await db.execute(stmt_assignee)
        assignee = result_assignee.scalar_one_or_none()
        if not assignee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assigned resident must be an active member of this residence."
            )

    # Perform updates
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "status" and value != task.status:
            if value == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
            else:
                task.completed_at = None
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    logger.info(f"Task {task_id} updated by user {current_user.id}.")
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft deletes a task."""
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == task.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this task."
        )

    task.deleted_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Task {task_id} soft-deleted by user {current_user.id}.")


# --- Task Execution Endpoints ---

@router.get("/tasks/{task_id}/executions", response_model=List[TaskExecutionResponse])
async def list_task_executions(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all execution logs for a specific task. Caller must belong to the task's residence."""
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == task.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this task."
        )

    stmt_execs = select(TaskExecution).where(TaskExecution.task_id == task_id)
    result_execs = await db.execute(stmt_execs)
    executions = result_execs.scalars().all()
    return executions


@router.post("/tasks/{task_id}/executions", response_model=TaskExecutionResponse, status_code=status.HTTP_201_CREATED)
async def log_task_execution(
    task_id: uuid.UUID,
    exec_in: TaskExecutionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Logs a new chore execution for the task.

    Automatically associates the execution with the caller's resident record.
    Sets the task status to COMPLETED and completes it.
    """
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == task.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this task."
        )

    # 1. Create task execution
    new_execution = TaskExecution(
        task_id=task_id,
        resident_id=caller_membership.id,
        executed_at=datetime.utcnow(),
        notes=exec_in.notes
    )
    db.add(new_execution)

    # 2. Mark task as COMPLETED
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(new_execution)
    logger.info(f"Task {task_id} execution logged by resident {caller_membership.id}.")
    return new_execution


# --- Task Attachments Endpoints ---

@router.post("/tasks/{task_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_task_attachment(
    task_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service)
) -> Any:
    """Uploads a file to Supabase Storage and links it to the task.

    Decoupled via BaseStorageService.
    """
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None)).options(selectinload(Task.attachments))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == task.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this task."
        )

    # 1. Read file bytes and compute checksum
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename."
        )
    file_bytes = await file.read()
    checksum = hashlib.md5(file_bytes).hexdigest()

    # 2. Generate a unique key for storage
    unique_id = uuid.uuid4()
    bucket = "attachments"
    # Format: tasks/{task_id}/{unique_uuid}-{filename}
    clean_filename = file.filename.replace(" ", "_")
    storage_key = f"tasks/{task_id}/{unique_id}-{clean_filename}"

    # 3. Upload file via decoupled service
    try:
        await storage.upload_file(
            bucket=bucket,
            file_bytes=file_bytes,
            destination_path=storage_key,
            content_type=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        logger.exception("Storage service upload failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {str(e)}"
        )

    # 4. Create Attachment record
    new_attachment = Attachment(
        id=unique_id,
        storage_provider="Supabase",
        storage_bucket=bucket,
        storage_key=storage_key,
        file_name=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(file_bytes),
        checksum=checksum
    )
    db.add(new_attachment)
    
    # Associate with Task (many-to-many join)
    task.attachments.append(new_attachment)
    await db.commit()
    await db.refresh(new_attachment)

    logger.info(f"File {file.filename} uploaded for task {task_id} by user {current_user.id}.")
    return new_attachment


@router.delete("/tasks/{task_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_attachment(
    task_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service)
) -> None:
    """Deletes an attachment from both the task association, database record, and Supabase Storage."""
    stmt = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None)).options(selectinload(Task.attachments))
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == task.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this task."
        )

    # Find the target attachment
    attachment = None
    for att in task.attachments:
        if att.id == attachment_id:
            attachment = att
            break

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not associated with this task"
        )

    # 1. Remove association
    task.attachments.remove(attachment)

    # 2. Delete file from storage
    storage_deleted = await storage.delete_file(
        bucket=attachment.storage_bucket,
        storage_key=attachment.storage_key
    )
    if not storage_deleted:
        logger.warning(f"Could not delete physical file {attachment.storage_key} from Supabase Storage.")

    # 3. Delete database record
    await db.delete(attachment)
    await db.commit()

    logger.info(f"Attachment {attachment_id} removed from task {task_id} by user {current_user.id}.")
