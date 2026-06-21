import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, Numeric, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, AuditMixin

if TYPE_CHECKING:
    from app.models.user import User


class FinancialSplitMethod(str, enum.Enum):
    EQUAL = "EQUAL"
    INCOME_WEIGHT = "INCOME_WEIGHT"
    CUSTOM = "CUSTOM"


class ResidentRole(str, enum.Enum):
    MASTER = "MASTER"
    RESIDENT = "RESIDENT"


class Residence(Base, AuditMixin):
    """Residence model representing a co-living household.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "residences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    timezone: Mapped[str] = mapped_column(
        String(100),
        default="America/Sao_Paulo",
        nullable=False
    )

    # Relationships
    settings: Mapped["ResidenceSetting"] = relationship(
        "ResidenceSetting",
        back_populates="residence",
        uselist=False,
        cascade="all, delete-orphan"
    )
    residents: Mapped[list["Resident"]] = relationship(
        "Resident",
        back_populates="residence",
        cascade="all, delete-orphan"
    )


class ResidenceSetting(Base, AuditMixin):
    """ResidenceSetting model storing configuration for a specific residence.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "residence_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    residence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("residences.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    financial_split_method: Mapped[FinancialSplitMethod] = mapped_column(
        Enum(FinancialSplitMethod, name="financial_split_method_enum"),
        default=FinancialSplitMethod.EQUAL,
        nullable=False
    )
    guest_retention_days: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    default_currency: Mapped[str] = mapped_column(
        String(10),
        default="BRL",
        nullable=False
    )

    # Relationships
    residence: Mapped["Residence"] = relationship("Residence", back_populates="settings")


class Resident(Base, AuditMixin):
    """Resident model representing a user associated to a residence.
    
    Conforms to docs/MODELO_FISICO.md specifications.
    """
    __tablename__ = "residents"
    __table_args__ = (
        UniqueConstraint("residence_id", "user_id"),
    )

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
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[ResidentRole] = mapped_column(
        Enum(ResidentRole, name="resident_role_enum"),
        default=ResidentRole.RESIDENT,
        nullable=False
    )
    income_weight: Mapped[float] = mapped_column(
        Numeric(10, 4),
        default=1.0000,
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    residence: Mapped["Residence"] = relationship("Residence", back_populates="residents")
    user: Mapped["User"] = relationship("User", back_populates="resident")
