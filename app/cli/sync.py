import asyncio
import logging
import sys

from app.db.session import AsyncSessionLocal
from app.sources.campus import CampusSourceConnector, SessionExpiredException
from app.services.ingestion import IngestionService
from app.services.notifier import TelegramNotifierService

# Configuración básica de logs para visibilidad en systemd journalctl asd
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cli.sync")

async def run_sync_pipeline() -> bool:
    """
    Ejecuta el pipeline completo de sincronización:
    1. Extracción vía Playwright (Campus INFD).
    2. Persistencia y deduplicación en SQLite.
    3. Notificación de eventos pendientes a Telegram.
    """
    logger.info("Iniciando pipeline de sincronización académica...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Scrapeo e Ingesta
            connector = CampusSourceConnector()
            ingestion_service = IngestionService(session)
            new_count, total_scraped = await ingestion_service.process_connector(connector)

            # 2. Despacho por Telegram
            notifier = TelegramNotifierService()
            sent_count = await notifier.notify_pending_events(session)

            logger.info(
                f"Sincronización finalizada exitosamente. "
                f"Extraídos: {total_scraped} | Nuevos guardados: {new_count} | Enviados a Telegram: {sent_count}"
            )
            return True

        except SessionExpiredException as se:
            logger.critical(f"Sesión del campus expirada: {se}")
            notifier = TelegramNotifierService()
            await notifier.send_admin_alert(
                "⚠️ <b>[CAMPUS INFD] Sesión Expirada</b>\n\n"
                "Las credenciales/cookies de Playwright caducaron.\n"
                "Por favor, renová el archivo <code>campus_storage_state.json</code>."
            )
            return False

        except Exception as e:
            logger.error(f"Error crítico durante la sincronización: {str(e)}", exc_info=True)
            return False


if __name__ == "__main__":
    success = asyncio.run(run_sync_pipeline())
    sys.exit(0 if success else 1)