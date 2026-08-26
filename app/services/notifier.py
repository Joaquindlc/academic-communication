import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.source_event import SourceEvent
from app.services.base_notifier import BaseNotifierService
from app.services.telegram_notifier import TelegramNotifierService
from app.services.whatsapp_notifier import WhatsAppNotifierService

logger = logging.getLogger(__name__)


class NotificationOrchestrator:

    def __init__(self):
        self.services: Dict[str, BaseNotifierService] = {}
        self._register_default_services()

    def _register_default_services(self):
        self.services["telegram"] = TelegramNotifierService()
        self.services["whatsapp"] = WhatsAppNotifierService()

    def register_service(
        self, channel_name: str, service: BaseNotifierService
    ):
        self.services[channel_name] = service

    def _get_active_targets(self) -> List[Tuple[str, str]]:
        """
        Retorna la lista de pares (canal, target_id) activos.
        """
        targets = []

        # Chat Individual de Telegram 
        if getattr(settings, "TELEGRAM_CHAT_ID", None):
            targets.append(("telegram", settings.TELEGRAM_CHAT_ID))

        # Grupo de Telegram
        if getattr(settings, "TELEGRAM_GROUP_CHAT_ID", None):
            targets.append(("telegram", settings.TELEGRAM_GROUP_CHAT_ID))

        # Chat Individual de Whatsapp 
        if getattr(settings, "WHATSAPP_TARGET_JID", None):
            targets.append(("whatsapp", settings.WHATSAPP_TARGET_JID))
            
        return targets

    async def notify_pending_events(self, session: AsyncSession) -> int:
        stmt = (
            select(SourceEvent)
            .where(SourceEvent.processed_at.is_(None))
            .order_by(SourceEvent.id.asc())
        )
        result = await session.execute(stmt)
        pending_events = result.scalars().all()

        if not pending_events:
            logger.info(
                "[ORCHESTRATOR] No hay eventos pendientes de notificación."
            )
            return 0

        targets = self._get_active_targets()
        if not targets:
            logger.warning("[ORCHESTRATOR] No hay canales/targets activos configurados.")
            return 0

        sent_count = 0
        for event in pending_events:
            event_success = True
            
            # Obtener el thread_id correspondiente a la materia del evento
            thread_id = settings.get_topic_id(event.course)

            for channel, target_id in targets:
                service = self.services.get(channel)
                if not service:
                    logger.warning(
                        f"[ORCHESTRATOR] Canal '{channel}' no registrado."
                    )
                    continue

                formatted_text = service.format_message(event)

                # Si es el grupo de Telegram y la materia tiene un tópico configurado, enviamos thread_id
                if channel == "telegram" and target_id == settings.TELEGRAM_GROUP_CHAT_ID and thread_id:
                    ok = await service.send_message(
                        target_id=target_id,
                        message_text=formatted_text,
                        thread_id=thread_id,
                    )
                else:
                    ok = await service.send_message(
                        target_id=target_id,
                        message_text=formatted_text,
                    )

                if not ok:
                    event_success = False

                # Rate limiting suave entre envíos de un mismo evento
                await asyncio.sleep(0.7)

            if event_success:
                event.processed_at = datetime.now(timezone.utc)
                sent_count += 1

            # Pausa de 1 segundo entre eventos para no saturar las APIs
            await asyncio.sleep(2.3)

        if sent_count > 0:
            await session.commit()

        logger.info(
            f"[ORCHESTRATOR] Se procesaron {sent_count} eventos correctamente."
        )
        return sent_count


# Instancia por defecto para importar en el CLI / sync.py
orchestrator = NotificationOrchestrator()