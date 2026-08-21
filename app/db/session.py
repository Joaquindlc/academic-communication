from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Garantizar el driver aiosqlite para SQLite asíncrono
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite://"):
    db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)

# SQLite asíncrono maneja los hilos a través de aiosqlite
engine = create_async_engine(
    db_url,
    echo=(settings.ENV == "development"),
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base declarativa estándar para SQLAlchemy 2.0."""
    pass


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency Provider para los endpoints de FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()