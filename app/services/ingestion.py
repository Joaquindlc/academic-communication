import logging
from typing import Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_event import SourceEvent
from app.sources.base import SourceConnector

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_connector(self, connector: SourceConnector) -> Tuple[int, int]:
        """
        Ejecuta el conector y persiste únicamente los eventos cuya combinación
        (source, external_id) no exista en la base de datos SQLite.
        
        Retorna: (nuevos_insertados, total_extraidos)
        """
        raw_events = await connector.fetch_events()
        if not raw_events:
            logger.info(f"[{connector.source_name.upper()}] No se encontraron eventos nuevos.")
            return 0, 0

        new_count = 0
        for item in raw_events:
            # Consulta la constraint única compuesta definida en tu modelo
            stmt = select(SourceEvent.id).where(
                SourceEvent.source == item.source,
                SourceEvent.external_id == item.external_id
            )
            result = await self.session.execute(stmt)
            exists = result.scalar_one_or_none()

            if not exists:
                db_event = SourceEvent(
                    source=item.source,
                    external_id=item.external_id,
                    event_type=item.event_type,
                    course=item.course,
                    title=item.title,
                    content=item.content,
                    source_url=item.source_url,
                    occurred_at=item.occurred_at,
                )
                self.session.add(db_event)
                new_count += 1

        if new_count > 0:
            await self.session.commit()

        logger.info(
            f"[{connector.source_name.upper()}] Ingesta completada: "
            f"{new_count} guardados de {len(raw_events)} extraídos."
        )
        return new_count, len(raw_events)