import asyncio
import logging
from app.sources.campus import CampusSourceConnector

logging.basicConfig(level=logging.INFO)

async def main():
    connector = CampusSourceConnector()
    print(f"Probando conexión a: {connector.base_url}")
    print(f"Uso de credenciales desde: {connector.storage_state_path}")
    
    events = await connector.fetch_events()
    print(f"\nTotal eventos extraídos: {len(events)}")
    for ev in events:
        print(f"-> [{ev.course}] {ev.title} | Link: {ev.source_url}")

if __name__ == "__main__":
    asyncio.run(main())