import uuid
import httpx
import logging
from typing import Any, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.residence import Resident

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=True)


async def validate_supabase_token(token: str) -> Dict[str, Any]:
    """Validates the JWT token by calling Supabase Auth API endpoint.

    Args:
        token (str): The bearer JWT token.

    Returns:
        Dict[str, Any]: The user data payload from Supabase.

    Raises:
        HTTPException: If the token is invalid or Supabase request fails.
    """
    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.warning(
                    f"Supabase auth validation failed: {response.status_code} - {response.text}"
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP connection to Supabase Auth failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency to retrieve the currently authenticated user.

    Validates token via Supabase and fetches the user from the local database.
    """
    token = credentials.credentials
    payload = await validate_supabase_token(token)

    # Supabase response contains the user UUID in "id"
    supabase_uid_str = payload.get("id")
    if not supabase_uid_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user identifier",
        )

    try:
        user_uuid = uuid.UUID(supabase_uid_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier format",
        )

    # Fetch user from local database
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        # In case the webhook has not run yet, we raise 401.
        # This forces client retry or handles un-synchronized users.
        logger.warning(f"User {user_uuid} validated by Supabase but not found in local DB.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not synchronized in local database",
        )

    return user


class RequiresResident:
    """Dependency class to check if current user is a resident of a specific residence."""

    def __init__(self, allowed_roles: list[str] | None = None) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        residence_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Resident:
        """Checks if the user has a valid resident record in the specified residence.

        Returns:
            Resident: The resident association record.
        
        Raises:
            HTTPException: 403 Forbidden if not a member, 403 if role not authorized.
        """
        stmt = select(Resident).where(
            Resident.residence_id == residence_id,
            Resident.user_id == current_user.id,
            Resident.left_at.is_(None),  # Only active residents
        )
        result = await db.execute(stmt)
        resident = result.scalar_one_or_none()

        if not resident:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not an active resident of this household",
            )

        if self.allowed_roles and resident.role.value not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions within this residence",
            )

        return resident
