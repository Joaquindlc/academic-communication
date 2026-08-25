import os
import asyncio
from typing import List
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.sources.base import SourceConnector  # Asegúrate de importar la clase base adecuada
from app.core.config import settings

SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly'
]

# Estructura de DTO/Schema para que IngestionService pueda leer item.source, item.external_id, etc.
class RawEventDTO:
    def __init__(self, source, external_id, event_type, course, title, content, source_url, occurred_at):
        self.source = source
        self.external_id = external_id
        self.event_type = event_type
        self.course = course
        self.title = title
        self.content = content
        self.source_url = source_url
        self.occurred_at = occurred_at


class ClassroomConnector(SourceConnector):
    source_name = "classroom"

    def __init__(self, token_path: str = "token.json"):
        self.token_path = token_path
        self._service = None

    def _get_service(self):
        if self._service:
            return self._service

        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                raise FileNotFoundError(
                    f"Token no encontrado o inválido en {self.token_path}. Ejecutá el flujo de auth."
                )

        self._service = build('classroom', 'v1', credentials=creds)
        return self._service

    async def fetch_events(self) -> List[RawEventDTO]:
        """
        Método asíncrono requerido por IngestionService. 
        Ejecuta las llamadas bloqueantes de google-api-python-client en un thread separado.
        """
        return await asyncio.to_thread(self._fetch_events_sync)

    def _fetch_events_sync(self) -> List[RawEventDTO]:
        service = self._get_service()
        events: List[RawEventDTO] = []

        # 1. Obtener cursos activos
        courses_res = service.courses().list(courseStates=['ACTIVE']).execute()
        courses = courses_res.get('courses', [])

        for course in courses:
            course_id = course['id']
            course_name = course.get('name', 'Curso sin nombre')

            # 2. Extraer Anuncios (Tablón)
            announcements_res = service.courses().announcements().list(
                courseId=course_id, pageSize=10
            ).execute()
            
            for ann in announcements_res.get('announcements', []):
                events.append(
                    RawEventDTO(
                        source=self.source_name,
                        external_id=f"announcement_{ann['id']}",
                        event_type="announcement",
                        course=course_name,
                        title=f"Anuncio en {course_name}",
                        content=ann.get('text', ''),
                        source_url=ann.get('alternateLink', ''),
                        occurred_at=datetime.fromisoformat(ann['creationTime'].replace('Z', '+00:00'))
                    )
                )

            # 3. Extraer Tareas / Entregas (CourseWork Submissions)
            submissions_res = service.courses().courseWork().studentSubmissions().list(
                courseId=course_id, courseWorkId='-'
            ).execute()

            for sub in submissions_res.get('studentSubmissions', []):
                events.append(
                    RawEventDTO(
                        source=self.source_name,
                        external_id=f"submission_{sub['id']}",
                        event_type="assignment_submission",
                        course=course_name,
                        title=f"Entrega de Tarea - {course_name}",
                        content=f"Estado de entrega: {sub.get('state', 'UNKNOWN')}",
                        source_url=sub.get('alternateLink', ''),
                        occurred_at=datetime.fromisoformat(sub['updateTime'].replace('Z', '+00:00'))
                    )
                )

        return events