import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.task import RecurrenceCreate, RecurrenceResponse, AttachmentResponse

class EventCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    start_at: datetime
    end_at: datetime
    generate_task: bool = False
    recurrence: Optional[RecurrenceCreate] = None


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    generate_task: Optional[bool] = None
    owner_resident_id: Optional[uuid.UUID] = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    residence_id: uuid.UUID
    owner_resident_id: uuid.UUID
    recurrence_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    start_at: datetime
    end_at: datetime
    generate_task: bool
    recurrence: Optional[RecurrenceResponse] = None
    attachments: List[AttachmentResponse] = []
