import uuid
from datetime import date, time
from typing import Optional
from pydantic import BaseModel, Field

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str

    class Config:
        from_attributes = True


class ProfileResponse(BaseModel):
    first_name: str
    last_name: str
    nickname: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    birth_date: Optional[date] = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    nickname: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    avatar_url: Optional[str] = None
    birth_date: Optional[date] = None


class PreferencesResponse(BaseModel):
    language: str
    theme: str
    push_enabled: bool
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None

    class Config:
        from_attributes = True


class PreferencesUpdate(BaseModel):
    language: Optional[str] = Field(None, max_length=10)
    theme: Optional[str] = Field(None, max_length=20)
    push_enabled: Optional[bool] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
