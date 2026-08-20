from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db, Base, engine

# Crear tablas automaticamente si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend de administracion de comunicaciones academicas."
)

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        # Consulta ligera para verificar que SQLite responde
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
    
