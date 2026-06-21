import logging
import uuid
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, or_
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, RequiresResident
from app.db.session import get_db
from app.models.user import User
from app.models.residence import Resident
from app.models.task import Task, TaskStatus
from app.models.event import Event
from app.models.message import Message
from app.models.notification import Notification, NotificationStatus
from app.schemas.dashboard import DashboardResponse, ResidenceDashboardResponse
from app.schemas.notification import NotificationResponse

logger = logging.getLogger(__name__)

router = APIRouter()


# --- Dashboard Endpoints ---

@router.get("/dashboard", response_model=DashboardResponse)
async def get_global_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieves the consolidated global dashboard for the current user.

    Aggregates active residences, pending tasks, upcoming events, and unread notifications.
    """
    # 1. Fetch residences where user is an active resident
    stmt_residences = select(Resident).where(
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    ).options(selectinload(Resident.residence))
    res_result = await db.execute(stmt_residences)
    residents = res_result.scalars().all()
    
    active_residences = [r.residence for r in residents if r.residence is not None]
    residence_ids = [r.residence_id for r in residents]

    pending_tasks: List[Task] = []
    upcoming_events: List[Event] = []

    if residence_ids:
        # 2. Fetch pending or in-progress tasks
        stmt_tasks = select(Task).where(
            Task.residence_id.in_(residence_ids),
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            Task.deleted_at.is_(None)
        ).options(
            selectinload(Task.recurrence),
            selectinload(Task.attachments)
        ).order_by(Task.due_at.asc())
        tasks_result = await db.execute(stmt_tasks)
        pending_tasks = list(tasks_result.scalars().all())

        # 3. Fetch upcoming events (end_at in the future)
        stmt_events = select(Event).where(
            Event.residence_id.in_(residence_ids),
            Event.end_at > datetime.utcnow(),
            Event.deleted_at.is_(None)
        ).options(
            selectinload(Event.recurrence),
            selectinload(Event.attachments)
        ).order_by(Event.start_at.asc())
        events_result = await db.execute(stmt_events)
        upcoming_events = list(events_result.scalars().all())

    # 4. Fetch unread notifications
    stmt_notifs = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.status != NotificationStatus.READ,
        Notification.deleted_at.is_(None)
    ).order_by(Notification.created_at.desc())
    notifs_result = await db.execute(stmt_notifs)
    unread_notifications = list(notifs_result.scalars().all())
    unread_notifications_count = len(unread_notifications)

    return {
        "active_residences": active_residences,
        "pending_tasks": pending_tasks,
        "upcoming_events": upcoming_events,
        "unread_notifications": unread_notifications,
        "unread_notifications_count": unread_notifications_count
    }


@router.get("/dashboard/residences/{residence_id}", response_model=ResidenceDashboardResponse)
async def get_residence_dashboard(
    residence_id: uuid.UUID,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Retrieves a residence-specific dashboard.

    Aggregates pending tasks, upcoming events, and pinned bulletin board messages for that residence.
    """
    # 1. Fetch pending tasks for the residence
    stmt_tasks = select(Task).where(
        Task.residence_id == residence_id,
        Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
        Task.deleted_at.is_(None)
    ).options(
        selectinload(Task.recurrence),
        selectinload(Task.attachments)
    ).order_by(Task.due_at.asc())
    tasks_result = await db.execute(stmt_tasks)
    pending_tasks = tasks_result.scalars().all()

    # 2. Fetch upcoming events for the residence
    stmt_events = select(Event).where(
        Event.residence_id == residence_id,
        Event.end_at > datetime.utcnow(),
        Event.deleted_at.is_(None)
    ).options(
        selectinload(Event.recurrence),
        selectinload(Event.attachments)
    ).order_by(Event.start_at.asc())
    events_result = await db.execute(stmt_events)
    upcoming_events = events_result.scalars().all()

    # 3. Fetch pinned active messages
    stmt_messages = select(Message).where(
        Message.residence_id == residence_id,
        Message.pinned.is_(True),
        Message.deleted_at.is_(None),
        or_(
            Message.expires_at.is_(None),
            Message.expires_at > datetime.utcnow()
        )
    ).options(
        selectinload(Message.reads),
        selectinload(Message.attachments)
    ).order_by(Message.created_at.desc())
    messages_result = await db.execute(stmt_messages)
    pinned_messages = messages_result.scalars().all()

    return {
        "residence_id": residence_id,
        "pending_tasks": pending_tasks,
        "upcoming_events": upcoming_events,
        "pinned_messages": pinned_messages
    }


# --- Basic Notifications Endpoints ---

@router.get("/notifications", response_model=List[NotificationResponse])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all active (non-deleted) notifications for the current user."""
    stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.deleted_at.is_(None)
    ).order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    return notifications


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_as_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Marks a specific notification as read."""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
        Notification.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.status = NotificationStatus.READ
    await db.commit()
    await db.refresh(notification)

    logger.info(f"Notification {notification_id} marked as read by user {current_user.id}.")
    return notification


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Marks all pending or sent notifications for the current user as read."""
    stmt = update(Notification).where(
        Notification.user_id == current_user.id,
        Notification.status != NotificationStatus.READ,
        Notification.deleted_at.is_(None)
    ).values(
        status=NotificationStatus.READ,
        updated_at=datetime.utcnow()
    )
    await db.execute(stmt)
    await db.commit()
    logger.info(f"All notifications marked as read for user {current_user.id}.")


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft deletes a notification."""
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
        Notification.deleted_at.is_(None)
    )
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.deleted_at = datetime.utcnow()
    await db.commit()
    logger.info(f"Notification {notification_id} soft-deleted by user {current_user.id}.")
