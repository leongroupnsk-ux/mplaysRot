"""
Shared fixtures for all tests.

env vars are set here — BEFORE any app.* import — so that pydantic-settings
can build Settings() without a real .env file.
"""
import os
import sys
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# ── env setup (must happen before any `app.*` import) ─────────────────────────

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-32ch!")
os.environ.setdefault("POSTGRES_PASSWORD", "testpass")
os.environ.setdefault("CLICKHOUSE_PASSWORD", "testpass")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
# Rate limiter uses settings.redis_url; default host is "redis" (Docker), override for tests
os.environ.setdefault("REDIS_HOST", "localhost")

# ── PYTHONPATH: project root for services/etl and services/ingestion imports ──

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../..")
)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# ── app imports (after env is ready) ──────────────────────────────────────────

from app.db.postgres import get_db  # noqa: E402
from app.main import app             # noqa: E402
from app.models.user import User     # noqa: E402


# ── DB mock factory ───────────────────────────────────────────────────────────

def make_mock_db() -> AsyncMock:
    """Returns a minimal AsyncSession mock suitable for auth routes."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    session.refresh = AsyncMock()

    # Default: no rows found (scalar_one_or_none → None)
    _default_result = MagicMock()
    _default_result.scalar_one_or_none.return_value = None
    _default_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=_default_result)

    return session


def make_user(email: str = "test@example.com", password_hash: str = "") -> MagicMock:
    """
    Returns a MagicMock shaped like a User ORM object.
    Using MagicMock avoids SQLAlchemy's descriptor machinery (which requires
    _sa_instance_state to be initialised) while still providing all the
    attributes that route handlers and deps access.
    """
    user = MagicMock(spec=User)
    user.id = str(uuid.uuid4())  # UserOut.id is str; str is also valid for create_access_token
    user.email = email
    user.password_hash = password_hash
    user.full_name = "Тест Пользователь"
    user.role = "owner"
    user.is_active = True
    return user


# ── HTTP client fixture ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def mock_db():
    return make_mock_db()


@pytest_asyncio.fixture
async def client(mock_db):
    async def _override_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, mock_db
    app.dependency_overrides.clear()
