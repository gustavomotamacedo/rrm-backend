import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.notification import NotificationStatus

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    source_entity_type: Optional[str] = None
    source_entity_id: Optional[uuid.UUID] = None
    type: str
    title: str
    body: str
    status: NotificationStatus
    created_at: datetime
    updated_at: datetime
