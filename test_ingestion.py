import asyncio
import logging
from app.db.session import AsyncSessionLocal
from app.services.ingestion import IngestionService
from app.sources.classroom import ClassroomConnector

logging.basicConfig(level=logging.INFO)

async def main():
    async with AsyncSessionLocal() as session:
        service = IngestionService(session)
        connector = ClassroomConnector(token_path="token.json")
        
        print("Iniciando ingesta de Google Classroom...")
        inserted, total = await service.process_connector(connector)
        print(f"Resultado: {inserted} eventos nuevos guardados de {total} procesados.")

if __name__ == "__main__":
    asyncio.run(main())