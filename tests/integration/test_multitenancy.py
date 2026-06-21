"""
Integration tests: Multi-tenancy isolation.

Verifies that users cannot read or modify data that belongs to a different
residence (cross-tenant access control).

Scenarios:
1. GET /tasks/{id}          — user not a member of the task's residence → 403.
2. PATCH /tasks/{id}        — user not a member → 403.
3. DELETE /tasks/{id}       — user not a member → 403.
4. GET /messages/{id}       — user not a member → 403.
5. POST /messages/{id}/read — user not a member → 403.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.session import get_db
from app.main import app
from app.core.security import get_current_user

from tests.integration.conftest import (
    USER_ID, OTHER_RESIDENCE_ID,
    TASK_ID, MESSAGE_ID,
    FakeResult,
    make_user, make_task, make_message,
)


# ---------------------------------------------------------------------------
# Helper: DB that returns a resource owned by OTHER_RESIDENCE, then no membership
# ---------------------------------------------------------------------------

def _db_foreign_task():
    """Task belongs to OTHER_RESIDENCE; caller has no membership there."""
    foreign_task = make_task(TASK_ID, OTHER_RESIDENCE_ID)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        FakeResult(foreign_task),    # SELECT Task
        FakeResult(None),            # SELECT Resident → not a member
    ])
    db.commit = AsyncMock()

    async def _fake_db():
        yield db

    return _fake_db


def _db_foreign_message():
    """Message belongs to OTHER_RESIDENCE; caller has no membership there."""
    foreign_message = make_message(MESSAGE_ID, OTHER_RESIDENCE_ID)

    db = AsyncMock()
    db.execute = AsyncMock(side_effect=[
        FakeResult(foreign_message),  # SELECT Message
        FakeResult(None),             # SELECT Resident → not a member
    ])
    db.commit = AsyncMock()

    async def _fake_db():
        yield db

    return _fake_db


# ---------------------------------------------------------------------------
# Task multi-tenancy tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_task_forbidden_for_non_member():
    """GET /tasks/{id} returns 403 when caller is not in the task's residence."""
    alice = make_user(USER_ID)
    app.dependency_overrides[get_current_user] = lambda: alice
    app.dependency_overrides[get_db] = _db_foreign_task()

    try:
        async with __import__("httpx").AsyncClient(
            transport=__import__("httpx").ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/tasks/{TASK_ID}",
                headers={"Authorization": "Bearer faketoken"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_task_forbidden_for_non_member():
    """PATCH /tasks/{id} returns 403 when caller is not in the task's residence."""
    alice = make_user(USER_ID)
    app.dependency_overrides[get_current_user] = lambda: alice
    app.dependency_overrides[get_db] = _db_foreign_task()

    try:
        async with __import__("httpx").AsyncClient(
            transport=__import__("httpx").ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/tasks/{TASK_ID}",
                json={"title": "Hack attempt"},
                headers={"Authorization": "Bearer faketoken"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_task_forbidden_for_non_member():
    """DELETE /tasks/{id} returns 403 when caller is not in the task's residence."""
    alice = make_user(USER_ID)
    app.dependency_overrides[get_current_user] = lambda: alice
    app.dependency_overrides[get_db] = _db_foreign_task()

    try:
        async with __import__("httpx").AsyncClient(
            transport=__import__("httpx").ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.delete(
                f"/api/v1/tasks/{TASK_ID}",
                headers={"Authorization": "Bearer faketoken"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Message multi-tenancy tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_message_forbidden_for_non_member():
    """GET /messages/{id} returns 403 when caller is not in the message's residence."""
    alice = make_user(USER_ID)
    app.dependency_overrides[get_current_user] = lambda: alice
    app.dependency_overrides[get_db] = _db_foreign_message()

    try:
        async with __import__("httpx").AsyncClient(
            transport=__import__("httpx").ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/messages/{MESSAGE_ID}",
                headers={"Authorization": "Bearer faketoken"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_mark_message_read_forbidden_for_non_member():
    """POST /messages/{id}/read returns 403 when caller is not in the message's residence."""
    alice = make_user(USER_ID)
    app.dependency_overrides[get_current_user] = lambda: alice
    app.dependency_overrides[get_db] = _db_foreign_message()

    try:
        async with __import__("httpx").AsyncClient(
            transport=__import__("httpx").ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/messages/{MESSAGE_ID}/read",
                headers={"Authorization": "Bearer faketoken"},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
