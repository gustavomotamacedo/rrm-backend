import uuid
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.models.task import RecurrenceFrequency, TaskStatus

class RecurrenceCreate(BaseModel):
    frequency: RecurrenceFrequency
    interval_value: int = Field(1, ge=1)
    by_week_day: Optional[str] = Field(None, max_length=50)
    by_month_day: Optional[int] = Field(None, ge=1, le=31)
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None


class RecurrenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    frequency: RecurrenceFrequency
    interval_value: int
    by_week_day: Optional[str] = None
    by_month_day: Optional[int] = None
    start_date: date
    end_date: Optional[date] = None


class TaskCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    assigned_resident_id: Optional[uuid.UUID] = None
    due_at: Optional[datetime] = None
    recurrence: Optional[RecurrenceCreate] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    assigned_resident_id: Optional[uuid.UUID] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[datetime] = None


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    mime_type: str
    file_size: int
    storage_key: str


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    residence_id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: TaskStatus
    assigned_resident_id: Optional[uuid.UUID] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    recurrence: Optional[RecurrenceResponse] = None
    attachments: List[AttachmentResponse] = []


class TaskExecutionCreate(BaseModel):
    notes: Optional[str] = None


class TaskExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_id: uuid.UUID
    resident_id: uuid.UUID
    executed_at: datetime
    notes: Optional[str] = None
