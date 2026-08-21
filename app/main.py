from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db, Base, engine
from app.cli.sync import run_sync_pipeline

# Crear tablas automáticamente si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend de administración de comunicaciones académicas."
)

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
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

@app.post("/api/admin/trigger-sync", tags=["Admin"])
async def trigger_manual_sync():
    """Dispara manualmente la ingesta académica desde HTTP."""
    success = await run_sync_pipeline()
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al procesar la ingesta o sesión expirada."
        )
    return {"status": "ok", "message": "Sincronización completada exitosamente"}