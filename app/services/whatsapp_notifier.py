import logging
import httpx
from app.core.config import settings
from app.models.source_event import SourceEvent
from app.services.base_notifier import BaseNotifierService

logger = logging.getLogger(__name__)


class WhatsAppNotifierService(BaseNotifierService):

    def __init__(self, bridge_url: str = getattr(settings, "WHATSAPP_BRIDGE_URL", "http://localhost:3000/send")):
        self.bridge_url = bridge_url

    def format_message(self, event: SourceEvent) -> str:
        """Aplica formato Markdown estándar de WhatsApp."""
        title = f"📌 *{event.title}*\n" if event.title else ""
        course = f"📚 *{event.course}*\n" if event.course else ""
        content = f"\n{event.content}\n" if event.content else ""
        url = f"\n🔗 {event.source_url}" if event.source_url else ""

        return f"{course}{title}{content}{url}"

    async def send_message(self, target_id: str, message_text: str) -> bool:
        if not self.bridge_url or not target_id:
            logger.warning("[WHATSAPP] Bridge URL o target_id no definidos.")
            return False

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(
                    self.bridge_url,
                    json={"to": target_id, "message": message_text},
                )
                return res.status_code == 200
            except Exception as e:
                logger.error(f"[WHATSAPP] Error de conexión con Baileys: {str(e)}")
                return False