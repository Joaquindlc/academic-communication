import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.source_event import SourceEvent

logger = logging.getLogger(__name__)


class TelegramNotifierService:
    def __init__(
        self,
        bot_token: str = settings.TELEGRAM_BOT_TOKEN,
        chat_id: str = settings.TELEGRAM_CHAT_ID,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def _format_message(self, event: SourceEvent) -> str:
        """Aplica formato HTML sencillo para las notificaciones de Telegram."""
        title = f"📌 <b>{event.title}</b>\n" if event.title else ""
        course = f"📚 <b>{event.course}</b>\n" if event.course else ""
        content = f"\n{event.content}\n" if event.content else ""
        url = f"\n🔗 <a href='{event.source_url}'>Ver en el Campus</a>" if event.source_url else ""

        return f"{course}{title}{content}{url}"

    async def notify_pending_events(self, session: AsyncSession) -> int:
        """
        Consulta los eventos con processed_at IS NULL, los envía por Telegram
        y actualiza la fecha de procesamiento.
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("[NOTIFIER] Token de Telegram o Chat ID no configurados.")
            return 0

        stmt = (
            select(SourceEvent)
            .where(SourceEvent.processed_at.is_(None))
            .order_by(SourceEvent.id.asc())
        )
        result = await session.execute(stmt)
        pending_events = result.scalars().all()

        if not pending_events:
            logger.info("[NOTIFIER] No hay eventos pendientes de notificación.")
            return 0

        sent_count = 0
        async with httpx.AsyncClient(timeout=10.0) as client:
            for event in pending_events:
                message_text = self._format_message(event)
                try:
                    res = await client.post(
                        self.api_url,
                        json={
                            "chat_id": self.chat_id,
                            "text": message_text,
                            "parse_mode": "HTML",
                            "disable_web_page_preview": False,
                        },
                    )
                    if res.status_code == 200:
                        event.processed_at = datetime.now(timezone.utc)
                        sent_count += 1
                    else:
                        logger.error(
                            f"[NOTIFIER] Error HTTP {res.status_code} al enviar evento ID {event.id}: {res.text}"
                        )

                except Exception as e:
                    logger.error(f"[NOTIFIER] Error de red enviando evento ID {event.id}: {str(e)}")

        if sent_count > 0:
            await session.commit()

        logger.info(f"[NOTIFIER] Se enviaron {sent_count} notificaciones con éxito.")
        return sent_count

    async def send_admin_alert(self, alert_text: str) -> bool:
        """Envía una alerta técnica directa (ej: sesión de Playwright expirada)."""
        if not self.bot_token or not self.chat_id:
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(
                    self.api_url,
                    json={
                        "chat_id": self.chat_id,
                        "text": alert_text,
                        "parse_mode": "HTML",
                    },
                )
                return res.status_code == 200
            except Exception as e:
                logger.error(f"[NOTIFIER] Error enviando alerta técnica: {str(e)}")
                return False