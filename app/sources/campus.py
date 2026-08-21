import logging
from pathlib import Path
from typing import List
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse, urljoin

from playwright.async_api import async_playwright, BrowserContext, Page

from app.config import settings
from app.sources.base import SourceConnector, SourceEventData

logger = logging.getLogger(__name__)


class SessionExpiredException(Exception):
    """Excepción lanzada cuando la sesión guardada en Playwright ha caducado."""
    pass


class CampusSourceConnector(SourceConnector):
    def __init__(
        self,
        base_url: str = settings.CAMPUS_BASE_URL,
        storage_state_path: Path = settings.STORAGE_STATE_PATH,
    ):
        # Aseguramos la barra final para que urljoin no sobreescriba /aula/
        self.base_url = base_url if base_url.endswith("/") else f"{base_url}/"
        self.storage_state_path = storage_state_path

    @property
    def source_name(self) -> str:
        return "campus"

    def _verify_storage_state(self) -> None:
        if not self.storage_state_path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de sesión en {self.storage_state_path}."
            )

    def _extract_external_id(self, url: str, index: int) -> str:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Extraer ID único según el parámetro URL del Campus
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
                target_url = urljoin(self.base_url, "acceso.cgi")
                logger.info(f"Conectando al Campus INFD en {target_url}...")
                
                await page.goto(
                    target_url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )

                # Control de sesión vencida
                if "login" in page.url or "iniciar" in page.url:
                    raise SessionExpiredException(
                        "La sesión del Campus expiró (redireccionado a pantalla de autenticación)."
                    )

                await page.wait_for_selector("ul.lista_sucesos, #Sucesos", timeout=10000)
                items = await page.query_selector_all("ul.lista_sucesos li.suceso")
                
                logger.info(f"[CAMPUS] Se detectaron {len(items)} sucesos en el panel de novedades.")

                for idx, item in enumerate(items):
                    try:
                        link_el = await item.query_selector("a[href]")
                        href = await link_el.get_attribute("href") if link_el else ""
                        href_clean = href.strip()

                        full_url = urljoin(self.base_url, href_clean) if href_clean else self.base_url
                        external_id = self._extract_external_id(full_url, idx)

                        class_attr = await link_el.get_attribute("class") if link_el else ""
                        event_type = class_attr.split()[0] if class_attr else "sucesos"

                        title_el = await item.query_selector("div.main")
                        title_text = (await title_el.inner_text()).strip() if title_el else "Sin título"

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
                            source_url=full_url,
                            occurred_at=datetime.now(timezone.utc)
                        )
                        events.append(event)
                    except Exception as item_err:
                        logger.warning(f"Error parseando suceso {idx}: {str(item_err)}")
                        continue

            except SessionExpiredException as se:
                logger.critical(f"[CAMPUS] {str(se)}")
                raise se
            except Exception as e:
                logger.error(f"Error durante la extracción del Campus: {str(e)}", exc_info=True)
                raise e
            finally:
                await context.close()
                await browser.close()

        return events