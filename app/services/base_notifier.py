from abc import abstractmethod
from app.models.source_event import SourceEvent

class BaseNotifierService(ABC):

    @abstractmethod
    def format_message(self, event: SourceEvent) -> str:
        """Aplica el formato visual correspondiente según la plataforma."""
        pass
    
    @abstractmethod
    async def send_message(self, target_id: str, message_text: str) -> bool:
        """Efectúa el envío del mensaje al target_id recibido."""
        pass 
