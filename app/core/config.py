import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Academic Communication System")
    VERSION: str = os.getenv("VERSION", "0.1.0")
    ENV: str = os.getenv("ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/academic.db")

    # --- Configuración Campus INFD ---
    CAMPUS_BASE_URL: str = os.getenv("CAMPUS_BASE_URL", "https://isfdyt210-bue.infd.edu.ar/aula/")
    
    # Manejo seguro de conversión entera
    try:
        CAMPUS_SYNC_INTERVAL_HOURS: int = int(os.getenv("CAMPUS_SYNC_INTERVAL_HOURS", "12"))
    except ValueError:
        CAMPUS_SYNC_INTERVAL_HOURS: int = 12

    # Rutas de Playwright para cookies/sesión
    STORAGE_STATE_PATH: Path = Path(
        os.getenv("STORAGE_STATE_PATH", "/opt/academic-communication/data/playwright/campus_storage_state.json")
    )

    # --- Configuración Telegram ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")


settings = Settings()