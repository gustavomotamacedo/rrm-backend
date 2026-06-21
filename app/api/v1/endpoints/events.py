import logging
import uuid
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, RequiresResident
from app.db.session import get_db
from app.models.user import User
from app.models.residence import Resident
from app.models.event import Event
from app.models.task import Recurrence
from app.schemas.event import EventCreate, EventUpdate, EventResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/residences/{residence_id}/events", response_model=List[EventResponse])
async def list_events(
    residence_id: uuid.UUID,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all events for a specific residence. Requires active membership."""
    stmt = select(Event).where(
        Event.residence_id == residence_id,
        Event.deleted_at.is_(None)
    ).options(
        selectinload(Event.recurrence),
        selectinload(Event.attachments)
    )
    result = await db.execute(stmt)
    events = result.scalars().all()
    return events


@router.post("/residences/{residence_id}/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    residence_id: uuid.UUID,
    event_in: EventCreate,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Creates a new event in the residence.

    If recurrence parameters are provided, creates the recurrence rule first.
    """
    # 1. Create Recurrence rule if provided
    recurrence = None
    if event_in.recurrence:
        recurrence = Recurrence(
            frequency=event_in.recurrence.frequency,
            interval_value=event_in.recurrence.interval_value,
            by_week_day=event_in.recurrence.by_week_day,
            by_month_day=event_in.recurrence.by_month_day,
            start_date=event_in.recurrence.start_date,
            end_date=event_in.recurrence.end_date
        )
        db.add(recurrence)
        await db.flush()

    # 2. Create Event
    new_event = Event(
        residence_id=residence_id,
        owner_resident_id=active_resident.id,
        recurrence_id=recurrence.id if recurrence else None,
        title=event_in.title,
        description=event_in.description,
        start_at=event_in.start_at,
        end_at=event_in.end_at,
        generate_task=event_in.generate_task
    )
    db.add(new_event)
    await db.commit()

    # Reload relationships for response serialization
    stmt_reload = select(Event).where(Event.id == new_event.id).options(
        selectinload(Event.recurrence),
        selectinload(Event.attachments)
    )
    result_reload = await db.execute(stmt_reload)
    event_response = result_reload.scalar_one()

    logger.info(f"Event {new_event.id} created by resident {active_resident.id}.")
    return event_response


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Gets details of an event. Caller must belong to the event's residence."""
    stmt = select(Event).where(
        Event.id == event_id,
        Event.deleted_at.is_(None)
    ).options(
        selectinload(Event.recurrence),
        selectinload(Event.attachments)
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Verify membership
    stmt_member = select(Resident).where(
        Resident.residence_id == event.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this event."
        )

    return event


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: uuid.UUID,
    event_in: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates event properties. Caller must belong to the event's residence."""
    stmt = select(Event).where(
        Event.id == event_id,
        Event.deleted_at.is_(None)
    ).options(
        selectinload(Event.recurrence),
        selectinload(Event.attachments)
    )
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == event.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this event."
        )

    # If updating owner_resident_id, verify that the new owner is a resident of this residence
    if event_in.owner_resident_id:
        stmt_owner = select(Resident).where(
            Resident.id == event_in.owner_resident_id,
            Resident.residence_id == event.residence_id,
            Resident.left_at.is_(None)
        )
        result_owner = await db.execute(stmt_owner)
        owner_exists = result_owner.scalar_one_or_none()
        if not owner_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New owner resident must be an active member of this residence."
            )

    # Perform updates
    update_data = event_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)
    logger.info(f"Event {event_id} updated by user {current_user.id}.")
    return event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft deletes an event."""
    stmt = select(Event).where(Event.id == event_id, Event.deleted_at.is_(None))
    result = await db.execute(stmt)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == event.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this event."
        )

    event.deleted_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Event {event_id} soft-deleted by user {current_user.id}.")
