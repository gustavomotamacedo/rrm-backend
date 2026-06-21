import uuid
import logging
from datetime import datetime, date
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User, Profile, UserPreference

logger = logging.getLogger(__name__)

router = APIRouter()


class WebhookPayload(BaseModel):
    type: str  # e.g., "INSERT", "UPDATE", "DELETE"
    table: str  # e.g., "users"
    schema_name: str = "auth"  # mapped from 'schema' in supabase payload
    record: Optional[Dict[str, Any]] = None
    old_record: Optional[Dict[str, Any]] = None


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    birth_date: Optional[date] = None
    preferences: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> Any:
    """Returns the profile and preferences of the currently logged-in user."""
    profile = current_user.profile
    preferences = current_user.preferences

    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": profile.first_name if profile else None,
        "last_name": profile.last_name if profile else None,
        "nickname": profile.nickname if profile else None,
        "phone": profile.phone if profile else None,
        "avatar_url": profile.avatar_url if profile else None,
        "birth_date": profile.birth_date if profile else None,
        "preferences": {
            "language": preferences.language if preferences else "pt-BR",
            "theme": preferences.theme if preferences else "light",
            "push_enabled": preferences.push_enabled if preferences else True,
            "quiet_hours_start": preferences.quiet_hours_start if preferences else None,
            "quiet_hours_end": preferences.quiet_hours_end if preferences else None,
        } if preferences else None
    }


@router.post("/register")
async def register() -> Any:
    """Placeholder for register. Authentication is delegated to Supabase Auth client-side."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration is managed directly via Supabase Auth client SDK. Backend user records are synchronized via webhooks."
    )


@router.post("/login")
async def login() -> Any:
    """Placeholder for login. Authentication is delegated to Supabase Auth client-side."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login is managed directly via Supabase Auth client SDK. Obtain JWT token on frontend and send in Authorization header."
    )


@router.post("/webhooks/supabase", status_code=status.HTTP_200_OK)
async def supabase_auth_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Webhook endpoint to synchronize Supabase Auth users with local tables."""
    # 1. Verify Webhook Secret if configured
    if settings.SUPABASE_WEBHOOK_SECRET:
        auth_header = request.headers.get("Authorization")
        secret_header = request.headers.get("X-Webhook-Secret")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        elif secret_header:
            token = secret_header

        if token != settings.SUPABASE_WEBHOOK_SECRET:
            logger.warning("Supabase webhook signature/secret verification failed.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )

    # 2. Parse payload manually to support Supabase DB Webhook structure
    # Supabase payload can have key 'schema' or 'schema_name' depending on configuration
    payload_json = await request.json()
    logger.info(f"Supabase Auth Webhook received: {payload_json}")

    event_type = payload_json.get("type") or payload_json.get("event")
    table = payload_json.get("table")
    record = payload_json.get("record")
    old_record = payload_json.get("old_record")

    if not event_type or table != "users":
        # Ignore events not belonging to auth.users table
        return {"status": "ignored", "reason": "Not a users table event"}

    # 3. Handle Events
    if event_type == "INSERT":
        if not record:
            raise HTTPException(status_code=400, detail="Missing record payload")

        user_id_str = record.get("id")
        email = record.get("email")

        if not user_id_str or not email:
            raise HTTPException(status_code=400, detail="Invalid record payload keys")

        user_id = uuid.UUID(user_id_str)

        # Check if user already exists (idempotency)
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            # If user exists, but was soft-deleted, restore them
            if existing_user.deleted_at:
                existing_user.deleted_at = None
                existing_user.deleted_by = None
                await db.flush()
                logger.info(f"Restored previously deleted user {user_id}")
            else:
                return {"status": "success", "detail": "User already exists"}
        else:
            # Create User
            new_user = User(
                id=user_id,
                email=email,
                password_hash=None,  # auth delegated to Supabase
            )
            db.add(new_user)
            await db.flush()

        # Parse user metadata from Supabase
        metadata = record.get("raw_user_meta_data") or {}
        first_name = metadata.get("first_name") or metadata.get("name") or "Usuário"
        last_name = metadata.get("last_name") or ""
        nickname = metadata.get("nickname")
        phone = metadata.get("phone") or record.get("phone")
        avatar_url = metadata.get("avatar_url")
        
        birth_date = None
        birth_date_str = metadata.get("birth_date")
        if birth_date_str:
            try:
                birth_date = date.fromisoformat(birth_date_str)
            except ValueError:
                logger.warning(f"Invalid birth_date format in metadata: {birth_date_str}")

        # Check if Profile already exists
        stmt_profile = select(Profile).where(Profile.user_id == user_id)
        result_profile = await db.execute(stmt_profile)
        existing_profile = result_profile.scalar_one_or_none()

        if not existing_profile:
            # Create Profile
            new_profile = Profile(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                nickname=nickname,
                phone=phone,
                avatar_url=avatar_url,
                birth_date=birth_date
            )
            db.add(new_profile)

        # Check if Preferences already exist
        stmt_pref = select(UserPreference).where(UserPreference.user_id == user_id)
        result_pref = await db.execute(stmt_pref)
        existing_pref = result_pref.scalar_one_or_none()

        if not existing_pref:
            # Create Default Preferences
            new_pref = UserPreference(
                user_id=user_id,
                language="pt-BR",
                theme="light",
                push_enabled=True
            )
            db.add(new_pref)

        logger.info(f"Successfully synchronized user signup for {email} ({user_id})")
        return {"status": "success", "detail": "User and profile synchronized"}

    elif event_type == "UPDATE":
        if not record:
            raise HTTPException(status_code=400, detail="Missing record payload")

        user_id_str = record.get("id")
        email = record.get("email")
        if not user_id_str:
            raise HTTPException(status_code=400, detail="Missing user id in update record")

        user_id = uuid.UUID(user_id_str)

        # Get User
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Update received for non-existent user {user_id}. Creating instead.")
            # Fallback to INSERT logic
            payload_json["type"] = "INSERT"
            # recursion to reuse insertion logic
            return await supabase_auth_webhook(request, db)

        # Update User email
        if email:
            user.email = email

        # Update Profile
        metadata = record.get("raw_user_meta_data") or {}
        stmt_profile = select(Profile).where(Profile.user_id == user_id)
        result_profile = await db.execute(stmt_profile)
        profile = result_profile.scalar_one_or_none()

        if profile:
            if "first_name" in metadata:
                profile.first_name = metadata["first_name"]
            elif "name" in metadata:
                profile.first_name = metadata["name"]
            
            if "last_name" in metadata:
                profile.last_name = metadata["last_name"]
            if "nickname" in metadata:
                profile.nickname = metadata["nickname"]
            if "phone" in metadata or record.get("phone"):
                profile.phone = metadata.get("phone") or record.get("phone")
            if "avatar_url" in metadata:
                profile.avatar_url = metadata["avatar_url"]
            
            if "birth_date" in metadata:
                birth_date_str = metadata["birth_date"]
                if birth_date_str:
                    try:
                        profile.birth_date = date.fromisoformat(birth_date_str)
                    except ValueError:
                        pass

        logger.info(f"Successfully synchronized user update for {user_id}")
        return {"status": "success", "detail": "User and profile updated"}

    elif event_type == "DELETE":
        # Handle User deletion
        # In Supabase Database Webhooks for DELETE, the deleted record is in old_record
        target_record = old_record or record
        if not target_record:
            raise HTTPException(status_code=400, detail="Missing record payload for DELETE")

        user_id_str = target_record.get("id")
        if not user_id_str:
            raise HTTPException(status_code=400, detail="Missing user id in delete record")

        user_id = uuid.UUID(user_id_str)

        # Soft delete User
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            current_time = datetime.utcnow()
            user.deleted_at = current_time
            
            # Also soft delete Profile
            stmt_profile = select(Profile).where(Profile.user_id == user_id)
            result_profile = await db.execute(stmt_profile)
            profile = result_profile.scalar_one_or_none()
            if profile:
                profile.deleted_at = current_time

            # Also soft delete UserPreference
            stmt_pref = select(UserPreference).where(UserPreference.user_id == user_id)
            result_pref = await db.execute(stmt_pref)
            preferences = result_pref.scalar_one_or_none()
            if preferences:
                preferences.deleted_at = current_time

            logger.info(f"Successfully synchronized soft-delete for user {user_id}")
            return {"status": "success", "detail": "User soft-deleted"}

        return {"status": "ignored", "detail": "User not found in local DB"}

    return {"status": "ignored", "reason": f"Unhandled event type: {event_type}"}
