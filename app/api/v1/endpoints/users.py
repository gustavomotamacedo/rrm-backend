import logging
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User, Profile, UserPreference
from app.schemas.user import (
    UserResponse,
    ProfileResponse,
    ProfileUpdate,
    PreferencesResponse,
    PreferencesUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/users/me", response_model=UserResponse)
async def read_user_me(current_user: User = Depends(get_current_user)) -> Any:
    """Gets the currently logged in user info (ID and Email)."""
    return current_user


@router.patch("/users/me")
async def update_user_me() -> Any:
    """Updates the user account. Email modifications are managed by Supabase Auth client SDK."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Account credentials (email, password) must be updated directly via Supabase Auth client SDK."
    )


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)

async def delete_user_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Performs soft delete on the currently logged in user account."""
    current_time = datetime.utcnow()
    
    # Soft delete User
    current_user.deleted_at = current_time
    
    # Soft delete Profile
    stmt_profile = select(Profile).where(Profile.user_id == current_user.id)
    result_profile = await db.execute(stmt_profile)
    profile = result_profile.scalar_one_or_none()
    if profile:
        profile.deleted_at = current_time

    # Soft delete Preferences
    stmt_pref = select(UserPreference).where(UserPreference.user_id == current_user.id)
    result_pref = await db.execute(stmt_pref)
    preferences = result_pref.scalar_one_or_none()
    if preferences:
        preferences.deleted_at = current_time

    await db.commit()
    logger.info(f"User {current_user.id} requested self-deletion.")


@router.get("/profile", response_model=ProfileResponse)
async def read_user_profile(current_user: User = Depends(get_current_user)) -> Any:
    """Gets the profile details of the current logged in user."""
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this user"
        )
    return profile


@router.patch("/profile", response_model=ProfileResponse)
async def update_user_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates the profile details of the current logged in user."""
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this user"
        )

    # Update only fields provided
    update_data = profile_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/preferences", response_model=PreferencesResponse)
async def read_user_preferences(current_user: User = Depends(get_current_user)) -> Any:
    """Gets the system preferences of the current logged in user."""
    preferences = current_user.preferences
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found for this user"
        )
    return preferences


@router.patch("/preferences", response_model=PreferencesResponse)
async def update_user_preferences(
    preferences_in: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates the system preferences of the current logged in user."""
    preferences = current_user.preferences
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found for this user"
        )

    # Update only fields provided
    update_data = preferences_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(preferences, field, value)

    await db.commit()
    await db.refresh(preferences)
    return preferences
