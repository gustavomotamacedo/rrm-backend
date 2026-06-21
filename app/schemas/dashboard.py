import uuid
from typing import List
from pydantic import BaseModel
from app.schemas.residence import ResidenceResponse
from app.schemas.task import TaskResponse
from app.schemas.event import EventResponse
from app.schemas.message import MessageResponse
from app.schemas.notification import NotificationResponse

class DashboardResponse(BaseModel):
    active_residences: List[ResidenceResponse]
    pending_tasks: List[TaskResponse]
    upcoming_events: List[EventResponse]
    unread_notifications: List[NotificationResponse]
    unread_notifications_count: int


class ResidenceDashboardResponse(BaseModel):
    residence_id: uuid.UUID
    pending_tasks: List[TaskResponse]
    upcoming_events: List[EventResponse]
    pinned_messages: List[MessageResponse]
