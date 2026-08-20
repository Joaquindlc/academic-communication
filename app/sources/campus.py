import logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from playwright.async_api import async_playwright, BrowserContext, Page

from app.sources.base import SourceConnector, SourceEventData

logger = logging.getLogger(__name__)


class CampusSourceConnector(SourceConnector):
    def __init__(
        self,
        base_url: str = "https://isfdyt210-bue.infd.edu.ar/aula",
        storage_state_path: Path = Path("/opt/academic-communication/data/playwright/campus_storage_state.json"),
        
    ):
        self.base_url = base_url
        self.storage_state_path = storage_state_path

    @property
    def source_name(self) -> str:
        return "campus"

    def _verify_storage_state(self) -> None:
        if not self.storage_state_path.exists():
            raise FileNotFoundError(
                f"No se encontro el archivo de session en {self.storage_state_path}."
            )


    def _extract_external_id(self, url: str, index: int) -> str:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Mapeo de parametros ID comunes en la plataforma Educativas
        for key in ["id_actividad", "wid_unidad", "wIdCategoria", "id_noticia", "id"]:
            if key in query_params:
                return f"campus_{key}_{query_params[key][0]}"
                
        return f"campus_evt_{int(datetime.now(timezone.utc).timestamp())}_{index}"
                

    async def fetch_events(self) -> List[SourceEventData]:
        self._verify_storage_state()
        events: List[SourceEventData] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context: BrowserContext = await browser.new_context(
                storage_state=str(self.storage_state_path),
                locale="es-AR",
                timezone_id="America/Argentina/Buenos_Aires",
            )
            page: Page = await context.new_page()

            try:
                logger.info(f"Conectando al Campus INFD en {self.base_url}...")
                await page.goto(
                    f"{self.base_url}/acceso.cgi",
                    wait_until="domcontentloaded",
                    timeout=30000
                )
                # Esperar a que el contenedor de sucesos recientes este en el DOM
                await page.wait_for_selector("ul.lista_sucesos, #Sucesos", timeout=10000)
                items = await page.query_selector_all("ul.lista_sucesos li.suceso")
                
                print(f"[CAMPUS] Se detectaron {len(items)} sucesos en el panel de novedades.")

                for idx, item in enumerate(items):
                    try:
                        # Enlace Principal
                        link_el = await item.query_selector("a[href]")
                        href = await link_el.get_attribute("href") if link_el else ""
                        full_url = href.strip()

                        # ID Unico extraido del href
                        external_id = self._extract_external_id(full_url, idx)

                        # Tipo de evento segun la clase css del tag <a> (actividad, unidad, nota)
                        class_attr = await link_el.get_attribute("class") if link_el else ""
                        event_type = class_attr.split()[0] if class_attr else "sucesos"

                        # Titulo Principal
                        title_el = await item.query_selector("div.main")
                        title_text = (await title_el.inner_text()).strip() if title_el else "Sin titulo"

                        # Nombre del aula / catedra
                        course_el = await item.query_selector("div.aula")
                        course_text = (await course_el.inner_text()).strip() if course_el else "General"

                        date_el = await item.query_selector("div.date")
                        date_text = (await date_el.inner_text()).strip() if date_el else ""

                        event = SourceEventData(
                            source=self.source_name,
                            external_id=external_id,
                            event_type=event_type,
                            course=course_text,
                            title=title_text,
                            content=f"Fecha reportada: {date_text}" if date_text else None,
                            source_url=full_url or page.url,
                            occurred_at=datetime.now(timezone.utc)
                        )
                        events.append(event)
                    except Exception as item_err:
                            logger.warning(f"Error parseando suceso {idx}: {str(item_err)}" )
                            continue
                                            
            except Exception as e:
                logger.error(f"Error durante la extraccion del Campus: {str(e)}", exc_info=True)
            finally:
                await context.close()
                await browser.close()
                
        return events
