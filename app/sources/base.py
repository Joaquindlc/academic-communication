# app/sources/base.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict

class SourceEventData(BaseModel):
    """
    DTO (Data Transfer Object) transitorio para transportar datos extraidos
    por los scrapers/conectores en memoria antes de ser persistidos
    """

    model_config = ConfigDict(frozen=True)
    
    source: str 
    external_id: str
    event_type: str
    
    course: str | None = None
    title: str | None = None
    content: str | None = None
    source_url: str | None = None
    
    occurred_at: datetime | None = None
    

class SourceConnector(ABC):
    """
    Interfaz abstracta para todos los conectores de fuentes externas.
    """
    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    async def fetch_events(self) -> list[SourceEventData]:
        """
         Extrae y devuelve una lista de novedades en formato DTO.
         No persiste directamente en base de datos
        """
        pass
