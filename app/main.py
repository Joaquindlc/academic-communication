from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_async_db, Base, engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend de administración de comunicaciones académicas."
)

@app.get("/health", tags=["System"])
async def health_check(db: AsyncSession = Depends(get_async_db)):
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy",
        "environment": settings.ENV,
        "system": "Debian 13 (Conectar Igualdad)",
        "database": {
            "engine": "SQLite",
            "status": db_status,
            "path": settings.DATABASE_URL
        }
    }