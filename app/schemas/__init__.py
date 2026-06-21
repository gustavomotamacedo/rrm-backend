# Package marker for schemas
from app.schemas.user import (
    UserResponse,
    ProfileResponse,
    ProfileUpdate,
    PreferencesResponse,
    PreferencesUpdate,
)
from app.schemas.residence import (
    ResidenceCreate,
    ResidenceUpdate,
    ResidenceResponse,
    ResidenceSettingResponse,
    ResidenceSettingUpdate,
    ResidentResponse,
    ResidentCreate,
    ResidentUpdate,
)
from app.schemas.task import (
    RecurrenceCreate,
    RecurrenceResponse,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskExecutionCreate,
    TaskExecutionResponse,
    AttachmentResponse,
)
from app.schemas.event import (
    EventCreate,
    EventUpdate,
    EventResponse,
)
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageReadResponse,
    MessageResponse,
)
from app.schemas.notification import (
    NotificationResponse,
)
from app.schemas.dashboard import (
    DashboardResponse,
    ResidenceDashboardResponse,
)

__all__ = [
    "UserResponse",
    "ProfileResponse",
    "ProfileUpdate",
    "PreferencesResponse",
    "PreferencesUpdate",
    "ResidenceCreate",
    "ResidenceUpdate",
    "ResidenceResponse",
    "ResidenceSettingResponse",
    "ResidenceSettingUpdate",
    "ResidentResponse",
    "ResidentCreate",
    "ResidentUpdate",
    "RecurrenceCreate",
    "RecurrenceResponse",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskExecutionCreate",
    "TaskExecutionResponse",
    "AttachmentResponse",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "MessageCreate",
    "MessageUpdate",
    "MessageReadResponse",
    "MessageResponse",
    "NotificationResponse",
    "DashboardResponse",
    "ResidenceDashboardResponse",
]

