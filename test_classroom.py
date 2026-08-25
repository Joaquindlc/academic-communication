import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.announcements.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly'
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
            flow.redirect_uri = 'http://localhost:8080/'
            
            auth_url, _ = flow.authorization_url(prompt='consent')

            print("\n1. Copiá y abrí esta URL en tu navegador de Windows:\n")
            print(auth_url)
            print("\n" + "="*60)
            print("2. Después de autorizar, la página mostrará 'No se puede acceder a este sitio web'.")
            print("   Copiá la URL COMPLETA que quedó en la barra de direcciones de tu navegador.")
            print("="*60 + "\n")
            
            auth_response = input("3. Pegá la URL completa acá: ").strip()
            flow.fetch_token(authorization_response=auth_response)
            creds = flow.credentials

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