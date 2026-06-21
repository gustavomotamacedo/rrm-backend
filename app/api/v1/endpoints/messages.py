import logging
import uuid
import hashlib
from datetime import datetime
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from app.core.security import get_current_user, RequiresResident
from app.db.session import get_db
from app.models.user import User
from app.models.residence import Resident
from app.models.message import Message, MessageRead
from app.models.attachment import Attachment
from app.services.storage import BaseStorageService, get_storage_service
from app.schemas.message import (
    MessageCreate,
    MessageUpdate,
    MessageResponse,
    MessageReadResponse,
)
from app.schemas.task import AttachmentResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/residences/{residence_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    residence_id: uuid.UUID,
    include_expired: bool = False,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Lists all active (non-deleted, and optionally non-expired) messages for a specific residence."""
    stmt = select(Message).where(
        Message.residence_id == residence_id,
        Message.deleted_at.is_(None)
    )

    if not include_expired:
        stmt = stmt.where(
            or_(
                Message.expires_at.is_(None),
                Message.expires_at > datetime.utcnow()
            )
        )

    stmt = stmt.options(
        selectinload(Message.reads),
        selectinload(Message.attachments)
    ).order_by(Message.pinned.desc(), Message.created_at.desc())

    result = await db.execute(stmt)
    messages = result.scalars().all()
    return messages


@router.post("/residences/{residence_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    residence_id: uuid.UUID,
    message_in: MessageCreate,
    active_resident: Resident = Depends(RequiresResident()),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Creates a new message/announcement in the residence."""
    new_message = Message(
        residence_id=residence_id,
        title=message_in.title,
        body=message_in.body,
        pinned=message_in.pinned,
        expires_at=message_in.expires_at,
        created_by=active_resident.user_id
    )
    db.add(new_message)
    await db.commit()

    # Reload relationships for response serialization
    stmt_reload = select(Message).where(Message.id == new_message.id).options(
        selectinload(Message.reads),
        selectinload(Message.attachments)
    )
    result_reload = await db.execute(stmt_reload)
    message_response = result_reload.scalar_one()

    logger.info(f"Message {new_message.id} created by user {active_resident.user_id}.")
    return message_response


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Gets details of a message. Caller must belong to the message's residence."""
    stmt = select(Message).where(
        Message.id == message_id,
        Message.deleted_at.is_(None)
    ).options(
        selectinload(Message.reads),
        selectinload(Message.attachments)
    )
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Verify membership
    stmt_member = select(Resident).where(
        Resident.residence_id == message.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this message."
        )

    return message


@router.patch("/messages/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: uuid.UUID,
    message_in: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Updates message properties. Caller must belong to the message's residence."""
    stmt = select(Message).where(
        Message.id == message_id,
        Message.deleted_at.is_(None)
    ).options(
        selectinload(Message.reads),
        selectinload(Message.attachments)
    )
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == message.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this message."
        )

    # Perform updates
    update_data = message_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(message, field, value)

    message.updated_by = current_user.id

    await db.commit()
    await db.refresh(message)
    logger.info(f"Message {message_id} updated by user {current_user.id}.")
    return message


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Soft deletes a message."""
    stmt = select(Message).where(Message.id == message_id, Message.deleted_at.is_(None))
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == message.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this message."
        )

    message.deleted_at = datetime.utcnow()
    message.deleted_by = current_user.id
    await db.commit()
    logger.info(f"Message {message_id} soft-deleted by user {current_user.id}.")


# --- Message Read Tracking ---

@router.post("/messages/{message_id}/read", response_model=MessageReadResponse, status_code=status.HTTP_201_CREATED)
async def mark_message_as_read(
    message_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Marks a bulletin board message as read by the current user."""
    stmt = select(Message).where(Message.id == message_id, Message.deleted_at.is_(None))
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == message.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this message."
        )

    # Check if already read
    stmt_read = select(MessageRead).where(
        MessageRead.message_id == message_id,
        MessageRead.resident_id == caller_membership.id
    )
    result_read = await db.execute(stmt_read)
    existing_read = result_read.scalar_one_or_none()
    if existing_read:
        return existing_read

    # Create new MessageRead entry
    new_read = MessageRead(
        message_id=message_id,
        resident_id=caller_membership.id,
        read_at=datetime.utcnow()
    )
    db.add(new_read)
    await db.commit()
    await db.refresh(new_read)

    logger.info(f"Message {message_id} marked as read by resident {caller_membership.id}.")
    return new_read


# --- Message Attachments Endpoints ---

@router.post("/messages/{message_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_message_attachment(
    message_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service)
) -> Any:
    """Uploads a file to Supabase Storage and links it to the message."""
    stmt = select(Message).where(Message.id == message_id, Message.deleted_at.is_(None)).options(selectinload(Message.attachments))
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == message.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this message."
        )

    # 1. Read file bytes and compute checksum
    file_bytes = await file.read()
    checksum = hashlib.md5(file_bytes).hexdigest()

    # 2. Generate a unique key for storage
    unique_id = uuid.uuid4()
    bucket = "attachments"
    # Format: messages/{message_id}/{unique_uuid}-{filename}
    clean_filename = file.filename.replace(" ", "_")
    storage_key = f"messages/{message_id}/{unique_id}-{clean_filename}"

    # 3. Upload file via decoupled service
    try:
        await storage.upload_file(
            bucket=bucket,
            file_bytes=file_bytes,
            destination_path=storage_key,
            content_type=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        logger.exception("Storage service upload failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Storage upload failed: {str(e)}"
        )

    # 4. Create Attachment record
    new_attachment = Attachment(
        id=unique_id,
        storage_provider="Supabase",
        storage_bucket=bucket,
        storage_key=storage_key,
        file_name=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(file_bytes),
        checksum=checksum
    )
    db.add(new_attachment)

    # Associate with Message
    message.attachments.append(new_attachment)
    await db.commit()
    await db.refresh(new_attachment)

    logger.info(f"File {file.filename} uploaded for message {message_id} by user {current_user.id}.")
    return new_attachment


@router.delete("/messages/{message_id}/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message_attachment(
    message_id: uuid.UUID,
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service)
) -> None:
    """Deletes an attachment from both the message association, database record, and Supabase Storage."""
    stmt = select(Message).where(Message.id == message_id, Message.deleted_at.is_(None)).options(selectinload(Message.attachments))
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    # Check caller membership
    stmt_member = select(Resident).where(
        Resident.residence_id == message.residence_id,
        Resident.user_id == current_user.id,
        Resident.left_at.is_(None)
    )
    result_member = await db.execute(stmt_member)
    caller_membership = result_member.scalar_one_or_none()
    if not caller_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. You do not belong to the residence that owns this message."
        )

    # Find the target attachment
    attachment = None
    for att in message.attachments:
        if att.id == attachment_id:
            attachment = att
            break

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not associated with this message"
        )

    # 1. Remove association
    message.attachments.remove(attachment)

    # 2. Delete file from storage
    storage_deleted = await storage.delete_file(
        bucket=attachment.storage_bucket,
        storage_key=attachment.storage_key
    )
    if not storage_deleted:
        logger.warning(f"Could not delete physical file {attachment.storage_key} from Supabase Storage.")

    # 3. Delete database record
    await db.delete(attachment)
    await db.commit()

    logger.info(f"Attachment {attachment_id} removed from message {message_id} by user {current_user.id}.")
