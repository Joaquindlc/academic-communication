from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SourceEvent(Base):
    """
    Modelo de persistencia para eventos capturados desde fuentes externas.
    Entidad intermedia que almacena los eventos crudos capturados desde
    fuentes externas (Campus, Google Classroom) antes de convertirse en notificaciones.
    """
    
    __tablename__ = "source_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    

    course: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )
    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    

    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(), 
        nullable=False,
    )
    
    
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
    )

    def __repr__(self) -> str:
        return f"<SourceEvent(id={self.id}, source='{self.source}', external_id='{self.external_id}')>"
