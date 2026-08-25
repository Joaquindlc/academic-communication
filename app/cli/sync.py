import asyncio
import logging
import sys

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.ingestion import IngestionService
from app.services.notifier import orchestrator
from app.services.telegram_notifier import TelegramNotifierService
from app.sources.campus import CampusSourceConnector, SessionExpiredException
from app.sources.classroom import ClassroomConnector

# Configuración básica de logs para visibilidad en systemd journalctl
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cli.sync")


async def run_sync_pipeline() -> bool:
    """
    Ejecuta el pipeline completo de sincronización:
    1. Extracción multicanal (Campus INFD vía Playwright + Google Classroom API).
    2. Persistencia y deduplicación en SQLite.
    3. Notificación de eventos pendientes a los canales activos (Telegram/WhatsApp).
    """
    logger.info("Iniciando pipeline de sincronización académica...")

    async with AsyncSessionLocal() as session:
        try:
            ingestion_service = IngestionService(session)

            # 1. Scrapeo e Ingesta: Campus INFD
            logger.info("Ejecutando conector Campus INFD...")
            campus_connector = CampusSourceConnector()
            campus_new, campus_total = await ingestion_service.process_connector(campus_connector)

            # 2. Ingesta: Google Classroom
            logger.info("Ejecutando conector Google Classroom...")
            classroom_connector = ClassroomConnector(token_path="token.json")
            classroom_new, classroom_total = await ingestion_service.process_connector(classroom_connector)

            total_new = campus_new + classroom_new
            total_scraped = campus_total + classroom_total

            # 3. Despacho Multi-canal vía Orquestador
            sent_count = await orchestrator.notify_pending_events(session)

            logger.info(
                f"Sincronización finalizada exitosamente. "
                f"Extraídos: {total_scraped} (Campus: {campus_total}, Classroom: {classroom_total}) | "
                f"Nuevos guardados: {total_new} | Eventos procesados: {sent_count}"
            )
            return True

        except SessionExpiredException as se:
            logger.critical(f"Sesión del campus expirada: {se}")
            # Mantenemos la alerta técnica directa vía Telegram
            telegram_notifier = TelegramNotifierService()
            target_admin = getattr(
                settings,
                "TELEGRAM_CHAT_ID",
                getattr(settings, "TELEGRAM_GROUP_CHAT_ID", None),
            )

            if target_admin:
                await telegram_notifier.send_admin_alert(
                    target_id=target_admin,
                    alert_text=(
                        "⚠️ <b>[CAMPUS INFD] Sesión Expirada</b>\n\n"
                        "Las credenciales/cookies de Playwright caducaron.\n"
                        "Por favor, renová el archivo <code>campus_storage_state.json</code>."
                    ),
                )
            return False

        except Exception as e:
            logger.error(
                f"Error crítico durante la sincronización: {str(e)}",
                exc_info=True,
            )
            return False


if __name__ == "__main__":
    success = asyncio.run(run_sync_pipeline())
    sys.exit(0 if success else 1)