import enum
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin

if TYPE_CHECKING:
    from app.models.user import User


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    READ = "READ"
    FAILED = "FAILED"


class Notification(Base, AuditMixin):
    """Notification model representing system notifications sent to users.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    source_entity_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    source_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status_enum"),
        default=NotificationStatus.PENDING,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
