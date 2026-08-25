import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.me.readonly'
]

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080, open_browser=False)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('classroom', 'v1', credentials=creds)

    print("\nConectando a Google Classroom...")
    results = service.courses().list(courseStates=['ACTIVE']).execute()
    courses = results.get('courses', [])

    if not courses:
        print("No se encontraron cursos activos.")
    else:
        print("\n--- Cursos Activos Encontrados ---")
        for course in courses:
            print(f"• {course['name']} (ID: {course['id']})")

if __name__ == '__main__':
    main()