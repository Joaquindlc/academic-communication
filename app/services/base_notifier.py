from abc import ABC, abstractmethod
from app.models.source_event import SourceEvent


class BaseNotifierService(ABC):

    @abstractmethod
    def format_message(self, event: SourceEvent) -> str:
        """Aplica el formato visual correspondiente (HTML, Markdown, etc.) según la plataforma."""
        pass

    @abstractmethod
    async def send_message(self, target_id: str, message_text: str) -> bool:
        """Efectúa el envío del mensaje de un evento al destinatario o canal objetivo."""
        pass

    @abstractmethod
    async def send_admin_alert(self, target_id: str, alert_text: str) -> bool:
        """Envía una alerta técnica directa del sistema (ej: sesión expirada)."""
        pass

    