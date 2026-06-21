import uuid
from datetime import datetime, date, time
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, Date, Time, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin

if TYPE_CHECKING:
    from app.models.residence import Resident


class User(Base, AuditMixin):
    """User model representing authentication and identity credentials.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        CITEXT,
        unique=True,
        nullable=False,
        index=True
    )
    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    preferences: Mapped["UserPreference"] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    resident: Mapped["Resident"] = relationship(
        "Resident",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


class Profile(Base, AuditMixin):
    """Profile model storing personal details of a user.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    nickname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True
    )
    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    birth_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profile")


class UserPreference(Base, AuditMixin):
    """UserPreference model storing settings like language and theme.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    language: Mapped[str] = mapped_column(
        String(10),
        default="pt-BR",
        nullable=False
    )
    theme: Mapped[str] = mapped_column(
        String(20),
        default="light",
        nullable=False
    )
    push_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    quiet_hours_start: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )
    quiet_hours_end: Mapped[time | None] = mapped_column(
        Time,
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preferences")
