# Package marker for models and import all models for Alembic discovery
from app.models.base import Base, AuditMixin
from app.models.user import User, Profile, UserPreference
from app.models.residence import Residence, ResidenceSetting, Resident, FinancialSplitMethod, ResidentRole
from app.models.task import Recurrence, Task, TaskExecution, RecurrenceFrequency, TaskStatus
from app.models.event import Event
from app.models.message import Message, MessageRead
from app.models.attachment import Attachment, task_attachments, event_attachments, message_attachments
from app.models.notification import Notification, NotificationStatus

__all__ = [
    "Base",
    "AuditMixin",
    "User",
    "Profile",
    "UserPreference",
    "Residence",
    "ResidenceSetting",
    "Resident",
    "FinancialSplitMethod",
    "ResidentRole",
    "Recurrence",
    "Task",
    "TaskExecution",
    "RecurrenceFrequency",
    "TaskStatus",
    "Event",
    "Message",
    "MessageRead",
    "Attachment",
    "task_attachments",
    "event_attachments",
    "message_attachments",
    "Notification",
    "NotificationStatus",
]
