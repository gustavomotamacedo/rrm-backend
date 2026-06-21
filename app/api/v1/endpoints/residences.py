import logging
import uuid
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_current_user, RequiresResident
from app.db.session import get_db
from app.models.user import User
from app.models.residence import Residence, ResidenceSetting, Resident, ResidentRole
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

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/residences", response_model=List[ResidenceResponse])
async def list_residences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all residences the currently authenticated user belongs to."""
    stmt = select(Residence).join(Resident).where(
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)  # Only active memberships
    )
    result = await db.execute(stmt)
    residences = result.scalars().all()
    return residences


@router.post("/residences", response_model=ResidenceResponse, status_code=status.HTTP_201_CREATED)
async def create_residence(
    residence_in: ResidenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Creates a new residence.

    The creating user is automatically assigned as a MASTER resident.
    """
    # 1. Create Residence
    new_residence = Residence(
        name=residence_in.name,
        timezone=residence_in.timezone
    )
    db.add(new_residence)
    await db.flush()  # Gen UUID for foreign keys

    # 2. Create Default Settings
    new_settings = ResidenceSetting(
        residence_id=new_residence.id
    )
    db.add(new_settings)

    # 3. Create Creator's Resident Entry as MASTER
    creator_resident = Resident(
        residence_id=new_residence.id,
        user_id=current_user.id,
        role=ResidentRole.MASTER,
        income_weight=1.0000,
        joined_at=datetime.utcnow()
    )
    db.add(creator_resident)

    await db.commit()
    await db.refresh(new_residence)
    logger.info(f"User {current_user.id} created residence {new_residence.id} ({new_residence.name}).")
    return new_residence


@router.get("/residences/{residence_id}", response_model=ResidenceResponse)
async def get_residence(
    residence_id: uuid.UUID,
    active_resident: Resident = Depends(RequiresResident())
) -> Any:
    """Gets details of a specific residence. Requires active membership."""
    return active_resident.residence


@router.patch("/residences/{residence_id}", response_model=ResidenceResponse)
async def update_residence(
    residence_id: uuid.UUID,
    residence_in: ResidenceUpdate,
    active_resident: Resident = Depends(RequiresResident(allowed_roles=[ResidentRole.MASTER])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates residence name or timezone. Requires MASTER role."""
    residence = active_resident.residence
    update_data = residence_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(residence, field, value)

    await db.commit()
    await db.refresh(residence)
    logger.info(f"Residence {residence.id} updated by resident {active_resident.id}.")
    return residence


@router.delete("/residences/{residence_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_residence(
    residence_id: uuid.UUID,
    active_resident: Resident = Depends(RequiresResident(allowed_roles=[ResidentRole.MASTER])),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Performs soft delete on a residence and all its settings/mural posts/tasks, etc."""
    current_time = datetime.utcnow()
    residence = active_resident.residence
    
    # Soft delete Residence
    residence.deleted_at = current_time

    # Soft delete Settings
    if residence.settings:
        residence.settings.deleted_at = current_time

    # Soft delete all active Residents
    for resident in residence.residents:
        if not resident.left_at:
            resident.left_at = current_time
        resident.deleted_at = current_time

    await db.commit()
    logger.info(f"Residence {residence_id} soft-deleted by master resident {active_resident.id}.")


@router.get("/residences/{residence_id}/settings", response_model=ResidenceSettingResponse)
async def get_residence_settings(
    residence_id: uuid.UUID,
    active_resident: Resident = Depends(RequiresResident())
) -> Any:
    """Gets settings of a specific residence. Requires active membership."""
    settings = active_resident.residence.settings
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found for this residence")
    return settings


@router.patch("/residences/{residence_id}/settings", response_model=ResidenceSettingResponse)
async def update_residence_settings(
    residence_id: uuid.UUID,
    settings_in: ResidenceSettingUpdate,
    active_resident: Resident = Depends(RequiresResident(allowed_roles=[ResidentRole.MASTER])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates settings of a residence. Requires MASTER role."""
    settings = active_resident.residence.settings
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found for this residence")

    update_data = settings_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    logger.info(f"Settings for residence {residence_id} updated by resident {active_resident.id}.")
    return settings


@router.get("/residences/{residence_id}/residents", response_model=List[ResidentResponse])
async def list_residence_residents(
    residence_id: uuid.UUID,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all residents of a specific residence. Requires active membership."""
    stmt = select(Resident).where(
        Resident.residence_id == residence_id,
        Resident.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    residents = result.scalars().all()
    return residents


@router.post("/residences/{residence_id}/residents", response_model=ResidentResponse, status_code=status.HTTP_201_CREATED)
async def add_residence_resident(
    residence_id: uuid.UUID,
    resident_in: ResidentCreate,
    active_resident: Resident = Depends(RequiresResident(allowed_roles=[ResidentRole.MASTER])),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Adds a new resident to the residence. Requires MASTER role.

    Verifies first if the user exists in the local database.
    """
    # 1. Verify if target User exists
    stmt_user = select(User).where(User.id == resident_in.user_id, User.deleted_at.is_(None))
    result_user = await db.execute(stmt_user)
    target_user = result_user.scalar_one_or_none()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in local database. User must sign up first."
        )

    # 2. Check if user is already a resident
    stmt_resident = select(Resident).where(
        Resident.residence_id == residence_id,
        Resident.user_id == resident_in.user_id,
        Resident.deleted_at.is_(None)
    )
    result_resident = await db.execute(stmt_resident)
    existing_resident = result_resident.scalar_one_or_none()

    if existing_resident:
        if existing_resident.left_at:
            # Re-join previously left resident
            existing_resident.left_at = None
            existing_resident.role = resident_in.role
            existing_resident.income_weight = resident_in.income_weight
            existing_resident.joined_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing_resident)
            return existing_resident
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already an active resident in this household."
            )

    # 3. Create new Resident link
    new_resident = Resident(
        residence_id=residence_id,
        user_id=resident_in.user_id,
        role=resident_in.role,
        income_weight=resident_in.income_weight,
        joined_at=datetime.utcnow()
    )
    db.add(new_resident)
    await db.commit()
    await db.refresh(new_resident)
    logger.info(f"Resident {new_resident.id} added to residence {residence_id} by master {active_resident.id}.")
    return new_resident


# --- Generic Resident Endpoints ---

@router.get("/residents/{resident_id}", response_model=ResidentResponse)
async def get_resident(
    resident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Gets details of a resident record.

    The calling user must belong to the same residence as the target resident.
    """
    # Fetch target resident
    stmt = select(Resident).where(Resident.id == resident_id, Resident.deleted_at.is_(None))
    result = await db.execute(stmt)
    target_resident = result.scalar_one_or_none()
    if not target_resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident record not found")

    # Check caller's active membership to same residence
    stmt_caller = select(Resident).where(
        Resident.residence_id == target_resident.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_caller = await db.execute(stmt_caller)
    caller_resident = result_caller.scalar_one_or_none()
    if not caller_resident:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the same residence as this resident."
        )

    return target_resident


@router.patch("/residents/{resident_id}", response_model=ResidentResponse)
async def update_resident(
    resident_id: uuid.UUID,
    resident_in: ResidentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates a resident record (e.g. role, weight, or setting left_at).

    The calling user must be a MASTER resident of that same residence.
    """
    stmt = select(Resident).where(Resident.id == resident_id, Resident.deleted_at.is_(None))
    result = await db.execute(stmt)
    target_resident = result.scalar_one_or_none()
    if not target_resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident record not found")

    # Check caller is a MASTER in that residence
    stmt_caller = select(Resident).where(
        Resident.residence_id == target_resident.residence_id,
        Resident.user_id == current_user.id,
        Resident.role == ResidentRole.MASTER,
        Resident.left_at.is_(None)
    )
    result_caller = await db.execute(stmt_caller)
    caller_resident = result_caller.scalar_one_or_none()
    if not caller_resident:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Requires MASTER role in the resident's household."
        )

    # Perform updates
    update_data = resident_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(target_resident, field, value)

    await db.commit()
    await db.refresh(target_resident)
    logger.info(f"Resident record {resident_id} updated by master user {current_user.id}.")
    return target_resident


@router.delete("/residents/{resident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resident(
    resident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft deletes a resident record (e.g. removing someone from the household).

    The calling user must be a MASTER resident of that same residence.
    """
    stmt = select(Resident).where(Resident.id == resident_id, Resident.deleted_at.is_(None))
    result = await db.execute(stmt)
    target_resident = result.scalar_one_or_none()
    if not target_resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident record not found")

    # Check caller is a MASTER in that residence
    stmt_caller = select(Resident).where(
        Resident.residence_id == target_resident.residence_id,
        Resident.user_id == current_user.id,
        Resident.role == ResidentRole.MASTER,
        Resident.left_at.is_(None)
    )
    result_caller = await db.execute(stmt_caller)
    caller_resident = result_caller.scalar_one_or_none()
    if not caller_resident:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Requires MASTER role in the resident's household."
        )

    # Cannot delete yourself as the sole MASTER resident
    if target_resident.user_id == current_user.id:
        # Check if there are other master residents
        stmt_masters = select(Resident).where(
            Resident.residence_id == target_resident.residence_id,
            Resident.role == ResidentRole.MASTER,
            Resident.left_at.is_(None),
            Resident.id != target_resident.id
        )
        result_masters = await db.execute(stmt_masters)
        other_master = result_masters.scalar_one_or_none()
        if not other_master:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete yourself if you are the sole MASTER resident. Transfer role or delete residence."
            )

    current_time = datetime.utcnow()
    target_resident.deleted_at = current_time
    if not target_resident.left_at:
        target_resident.left_at = current_time

    await db.commit()
    logger.info(f"Resident record {resident_id} soft-deleted by master user {current_user.id}.")
