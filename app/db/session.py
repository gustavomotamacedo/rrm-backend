from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Use test database URL if we are in testing mode
database_url = settings.DATABASE_URL
if settings.ENV == "test" and settings.DATABASE_TEST_URL:
    database_url = settings.DATABASE_TEST_URL

# Create async database engine
engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
    echo=settings.ENV == "development",
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# FastAPI session dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an asynchronous database session.

    Yields:
        AsyncSession: The database session.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
