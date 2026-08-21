import asyncio
import sys
import logging
from app.main import run_campus_ingestion_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def main():
    try:
        result = await run_campus_ingestion_job()
        print(f"Sincronización exitosa: {result}")
        sys.exit(0)
    except Exception as e:
        print(f"Error en ejecución CLI: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())