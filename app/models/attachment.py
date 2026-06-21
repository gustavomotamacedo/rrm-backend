import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Table, Column, String, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.event import Event
    from app.models.message import Message


# Association tables for many-to-many relationships
task_attachments = Table(
    "task_attachments",
    Base.metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("attachment_id", UUID(as_uuid=True), ForeignKey("attachments.id", ondelete="CASCADE"), primary_key=True)
)

event_attachments = Table(
    "event_attachments",
    Base.metadata,
    Column("event_id", UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    Column("attachment_id", UUID(as_uuid=True), ForeignKey("attachments.id", ondelete="CASCADE"), primary_key=True)
)

message_attachments = Table(
    "message_attachments",
    Base.metadata,
    Column("message_id", UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True),
    Column("attachment_id", UUID(as_uuid=True), ForeignKey("attachments.id", ondelete="CASCADE"), primary_key=True)
)


class Attachment(Base, AuditMixin):
    """Attachment model representing files uploaded to storage.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    storage_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    storage_bucket: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    storage_key: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    mime_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    checksum: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Relationships
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        secondary=task_attachments,
        back_populates="attachments"
    )
    events: Mapped[list["Event"]] = relationship(
        "Event",
        secondary=event_attachments,
        back_populates="attachments"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        secondary=message_attachments,
        back_populates="attachments"
    )
