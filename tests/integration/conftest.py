"""
Integration test fixtures.

Uses dependency_overrides to replace all I/O boundaries (DB session, auth,
storage) with lightweight in-memory fakes.  No real database or Supabase
connection is required.
"""
import uuid
from datetime import datetime
from typing import AsyncGenerator, Any
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import get_current_user, RequiresResident
from app.db.session import get_db
from app.models.user import User
from app.models.residence import Resident, ResidentRole
from app.models.task import Task, TaskStatus
from app.models.attachment import Attachment
from app.models.message import Message
from app.services.storage import BaseStorageService, get_storage_service


USER_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
RESIDENCE_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
RESIDENT_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
TASK_ID = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
MESSAGE_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
ATTACHMENT_ID = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")

OTHER_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_RESIDENCE_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def make_user(user_id=USER_ID, email="alice@example.com"):
    u = MagicMock(spec=User)
    u.id = user_id
    u.email = email
    u.deleted_at = None
    return u


def make_resident(resident_id=RESIDENT_ID, residence_id=RESIDENCE_ID, user_id=USER_ID, role=ResidentRole.RESIDENT):
    r = MagicMock(spec=Resident)
    r.id = resident_id
    r.residence_id = residence_id
    r.user_id = user_id
    r.role = role
    r.left_at = None
    r.income_weight = 1.0
    r.joined_at = datetime.utcnow()
    return r


def make_task(task_id=TASK_ID, residence_id=RESIDENCE_ID):
    t = MagicMock(spec=Task)
    t.id = task_id
    t.residence_id = residence_id
    t.title = "Clean kitchen"
    t.description = None
    t.status = TaskStatus.PENDING
    t.assigned_resident_id = None
    t.due_at = None
    t.completed_at = None
    t.deleted_at = None
    t.recurrence = None
    t.attachments = []
    return t


def make_message(message_id=MESSAGE_ID, residence_id=RESIDENCE_ID):
    m = MagicMock(spec=Message)
    m.id = message_id
    m.residence_id = residence_id
    m.title = "House meeting"
    m.body = "Tomorrow at 19h"
    m.pinned = False
    m.expires_at = None
    m.created_at = datetime.utcnow()
    m.updated_at = datetime.utcnow()
    m.created_by = USER_ID
    m.deleted_at = None
    m.reads = []
    m.attachments = []
    return m


def make_attachment(attachment_id=ATTACHMENT_ID, storage_key="attachments/tasks/file.txt", storage_bucket="attachments"):
    a = MagicMock(spec=Attachment)
    a.id = attachment_id
    a.storage_provider = "Supabase"
    a.storage_bucket = storage_bucket
    a.storage_key = storage_key
    a.file_name = "file.txt"
    a.mime_type = "text/plain"
    a.file_size = 5
    a.checksum = "abc123"
    return a


class FakeStorageService(BaseStorageService):
    def __init__(self):
        self.uploaded = []
        self.deleted = []

    async def upload_file(self, bucket, file_bytes, destination_path, content_type):
        self.uploaded.append({"bucket": bucket, "path": destination_path, "size": len(file_bytes)})
        return destination_path

    async def download_file(self, bucket, storage_key):
        return b"fake-content"

    async def delete_file(self, bucket, storage_key):
        self.deleted.append(storage_key)
        return True

    async def get_presigned_url(self, bucket, storage_key, expires_in=3600):
        return f"https://fake.storage/{bucket}/{storage_key}?token=fake"


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalar_one(self):
        if self._value is None:
            raise Exception("No row found")
        return self._value

    def scalars(self):
        return self

    def all(self):
        if self._value is None:
            return []
        return self._value if isinstance(self._value, list) else [self._value]


@pytest.fixture
def fake_storage():
    return FakeStorageService()


@pytest.fixture
def alice():
    return make_user(USER_ID, "alice@example.com")


@pytest.fixture
def alice_resident():
    return make_resident(RESIDENT_ID, RESIDENCE_ID, USER_ID)


@pytest.fixture
def sample_task():
    return make_task(TASK_ID, RESIDENCE_ID)


@pytest.fixture
def sample_message():
    return make_message(MESSAGE_ID, RESIDENCE_ID)


@pytest_asyncio.fixture
async def integration_client(alice, alice_resident, fake_storage):
    app.dependency_overrides[get_current_user] = lambda: alice
    app.dependency_overrides[get_storage_service] = lambda: fake_storage

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
