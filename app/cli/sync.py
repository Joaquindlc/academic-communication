import asyncio
import logging
import sys

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.ingestion import IngestionService
from app.services.notifier import orchestrator
from app.services.telegram_notifier import TelegramNotifierService
from app.sources.campus import CampusSourceConnector, SessionExpiredException

# Configuración básica de logs para visibilidad en systemd journalctl
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cli.sync")


async def run_sync_pipeline() -> bool:
    """
    Ejecuta el pipeline completo de sincronización:
    1. Extracción vía Playwright (Campus INFD).
    2. Persistencia y deduplicación en SQLite.
    3. Notificación de eventos pendientes a los canales activos (Telegram/WhatsApp).
    """
    logger.info("Iniciando pipeline de sincronización académica...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Scrapeo e Ingesta
            connector = CampusSourceConnector()
            ingestion_service = IngestionService(session)
            new_count, total_scraped = (
                await ingestion_service.process_connector(connector)
            )

            # 2. Despacho Multi-canal vía Orquestador
            sent_count = await orchestrator.notify_pending_events(session)

            logger.info(
                f"Sincronización finalizada exitosamente. "
                f"Extraídos: {total_scraped} | Nuevos guardados: {new_count} | Eventos procesados: {sent_count}"
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