import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.task import AttachmentResponse

class MessageCreate(BaseModel):
    title: str = Field(..., max_length=255)
    body: str
    pinned: bool = False
    expires_at: Optional[datetime] = None


class MessageUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    pinned: Optional[bool] = None
    expires_at: Optional[datetime] = None


class MessageReadResponse(BaseModel):
    id: uuid.UUID
    message_id: uuid.UUID
    resident_id: uuid.UUID
    read_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: uuid.UUID
    residence_id: uuid.UUID
    title: str
    body: str
    pinned: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    reads: List[MessageReadResponse] = []
    attachments: List[AttachmentResponse] = []

    class Config:
        from_attributes = True
