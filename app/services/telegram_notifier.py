import logging
import httpx
from app.core.config import settings
from app.models.source_event import SourceEvent
from app.services.base_notifier import BaseNotifierService

logger = logging.getLogger(__name__)


class TelegramNotifierService(BaseNotifierService):

    def __init__(self, bot_token: str = settings.TELEGRAM_BOT_TOKEN):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def format_message(self, event: SourceEvent) -> str:
        """Aplica formato HTML para las notificaciones de Telegram."""
        title = f"📌 <b>{event.title}</b>\n" if event.title else ""  
        content = f"\n{event.content}\n" if event.content else ""
        course = f"📚 <b>{event.course}</b>\n" if event.course else ""
        url = (
            f"\n🔗 <a href='{event.source_url}'>Ver en el Campus</a>"
            if event.source_url
            else ""
        )
        

        return f"{title}{content}{course}{url}"

    async def send_message(self, target_id: str, message_text: str) -> bool:
        if not self.bot_token or not target_id:
            logger.warning(
                "[TELEGRAM] Token o target_id de Telegram no configurados."
            )
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(
                    self.api_url,
                    json={
                        "chat_id": target_id,
                        "text": message_text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False,
                    },
                )
                if res.status_code == 200:
                    return True
                logger.error(
                    f"[TELEGRAM] Error HTTP {res.status_code}: {res.text}"
                )
                return False
            except Exception as e:
                logger.error(f"[TELEGRAM] Error de red: {str(e)}")
                return False

    async def send_admin_alert(
        self, target_id: str, alert_text: str
    ) -> bool:
        """Envía una alerta técnica directa (ej: sesión de Playwright expirada)."""
        return await self.send_message(target_id, alert_text)