import json
import logging
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Academic Communication System")
    VERSION: str = os.getenv("VERSION", "0.1.0")
    ENV: str = os.getenv("ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/academic.db")

    # --- Configuración Campus INFD ---
    CAMPUS_BASE_URL: str = os.getenv("CAMPUS_BASE_URL", "https://isfdyt210-bue.infd.edu.ar/aula/")
    
    try:
        CAMPUS_SYNC_INTERVAL_HOURS: int = int(os.getenv("CAMPUS_SYNC_INTERVAL_HOURS", "12"))
    except ValueError:
        CAMPUS_SYNC_INTERVAL_HOURS: int = 12

    STORAGE_STATE_PATH: Path = Path(
        os.getenv("STORAGE_STATE_PATH", "/opt/academic-communication/data/playwright/campus_storage_state.json")
    )

    # --- Configuración Telegram ---
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    TELEGRAM_GROUP_CHAT_ID: str = os.getenv("TELEGRAM_GROUP_CHAT_ID", "")

    # --- Mapeo Dinámico de Tópicos desde .env ---
    @property
    def COURSE_TOPIC_MAP(self) -> dict[str, int]:
        raw_json = os.getenv("TELEGRAM_COURSE_TOPIC_MAP", "{}")
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error(f"[CONFIG] Error al parsear TELEGRAM_COURSE_TOPIC_MAP: {e}")
            return {}

    def get_topic_id(self, course_name: Optional[str]) -> Optional[int]:
        if not course_name:
            return None

        clean_course = course_name.strip().lower()

        # Búsqueda por coincidencia parcial (soporta variaciones leves en el nombre)
        for key, thread_id in self.COURSE_TOPIC_MAP.items():
            if key.strip().lower() in clean_course or clean_course in key.strip().lower():
                return thread_id

        return None


settings = Settings()