# Package marker for schemas
from app.schemas.user import (
    UserResponse,
    ProfileResponse,
    ProfileUpdate,
    PreferencesResponse,
    PreferencesUpdate,
)
from app.schemas.residence import (
    ResidenceCreate,
    ResidenceUpdate,
    ResidenceResponse,
    ResidenceSettingResponse,
    ResidenceSettingUpdate,
    ResidentResponse,
    ResidentCreate,
    ResidentUpdate,
)

__all__ = [
    "UserResponse",
    "ProfileResponse",
    "ProfileUpdate",
    "PreferencesResponse",
    "PreferencesUpdate",
    "ResidenceCreate",
    "ResidenceUpdate",
    "ResidenceResponse",
    "ResidenceSettingResponse",
    "ResidenceSettingUpdate",
    "ResidentResponse",
    "ResidentCreate",
    "ResidentUpdate",
]

