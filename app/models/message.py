import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin

if TYPE_CHECKING:
    from app.models.attachment import Attachment


class Message(Base, AuditMixin):
    """Message model representing bulletin board posts for communication.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "messages"

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
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    reads: Mapped[list["MessageRead"]] = relationship(
        "MessageRead",
        back_populates="message",
        cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        secondary="message_attachments",
        back_populates="messages"
    )


class MessageRead(Base, AuditMixin):
    """MessageRead model tracking which residents have read which messages.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "message_reads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False
    )
    resident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    message: Mapped["Message"] = relationship("Message", back_populates="reads")
