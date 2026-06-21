import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin

if TYPE_CHECKING:
    from app.models.task import Recurrence
    from app.models.attachment import Attachment


class Event(Base, AuditMixin):
    """Event model representing calendar items scheduled for a residence.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    residence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("residences.id", ondelete="CASCADE"),
        nullable=False
    )
    owner_resident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False
    )
    recurrence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recurrences.id", ondelete="SET NULL"),
        nullable=True
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    generate_task: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Relationships
    recurrence: Mapped["Recurrence"] = relationship("Recurrence")
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        secondary="event_attachments",
        back_populates="events"
    )
