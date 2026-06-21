import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.residence import FinancialSplitMethod, ResidentRole

class ResidenceCreate(BaseModel):
    name: str = Field(..., max_length=200)
    timezone: str = Field("America/Sao_Paulo", max_length=100)


class ResidenceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    timezone: Optional[str] = Field(None, max_length=100)


class ResidenceResponse(BaseModel):
    id: uuid.UUID
    name: str
    timezone: str

    class Config:
        from_attributes = True


class ResidenceSettingResponse(BaseModel):
    financial_split_method: FinancialSplitMethod
    guest_retention_days: int
    notifications_enabled: bool
    default_currency: str

    class Config:
        from_attributes = True


class ResidenceSettingUpdate(BaseModel):
    financial_split_method: Optional[FinancialSplitMethod] = None
    guest_retention_days: Optional[int] = None
    notifications_enabled: Optional[bool] = None
    default_currency: Optional[str] = Field(None, max_length=10)


class ResidentResponse(BaseModel):
    id: uuid.UUID
    residence_id: uuid.UUID
    user_id: uuid.UUID
    role: ResidentRole
    income_weight: float
    joined_at: datetime
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResidentCreate(BaseModel):
    user_id: uuid.UUID
    role: ResidentRole = ResidentRole.RESIDENT
    income_weight: float = 1.0000


class ResidentUpdate(BaseModel):
    role: Optional[ResidentRole] = None
    income_weight: Optional[float] = None
    left_at: Optional[datetime] = None
