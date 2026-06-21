import enum
import uuid
from datetime import datetime, date
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, Integer, DateTime, Date, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin

if TYPE_CHECKING:
    from app.models.attachment import Attachment


class RecurrenceFrequency(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Recurrence(Base, AuditMixin):
    """Recurrence model defining rules for recurring tasks or events.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "recurrences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    frequency: Mapped[RecurrenceFrequency] = mapped_column(
        Enum(RecurrenceFrequency, name="recurrence_frequency_enum"),
        nullable=False
    )
    interval_value: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    by_week_day: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )
    by_month_day: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        default=date.today,
        nullable=False
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    # Relationships
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="recurrence")


class Task(Base, AuditMixin):
    """Task model representing a household chore or action item.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "tasks"

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
    assigned_resident_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("residents.id", ondelete="SET NULL"),
        nullable=True
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
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum"),
        default=TaskStatus.PENDING,
        nullable=False
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    recurrence: Mapped["Recurrence"] = relationship("Recurrence", back_populates="tasks")
    executions: Mapped[list["TaskExecution"]] = relationship(
        "TaskExecution",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment",
        secondary="task_attachments",
        back_populates="tasks"
    )


class TaskExecution(Base, AuditMixin):
    """TaskExecution model logging the completed occurrences of a task.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "task_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    resident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="executions")
