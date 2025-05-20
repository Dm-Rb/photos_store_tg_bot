import os
import mimetypes
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from config import config

class GoogleDriveUploader:
    """
    Класс для загрузки файлов на Google Drive.
    Хранит авторизацию и целевую папку загрузки (folder_id).
    """

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(
        self,
        folder_id: str,
        credentials_path: str = 'client_secret_google.json',
        token_path: str = 'token.json'
    ):
        """
        Инициализация:
        - folder_id: ID целевой папки на Google Drive.
        - credentials_path: путь к client_secret JSON.
        - token_path: путь к файлу с сохранённым токеном.
        """
        self.folder_id = folder_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)

    def _authenticate(self):
        """
        Авторизация по OAuth2. Сохраняет/обновляет токен.
        """
        creds = None

        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return creds

    def _upload_file_sync(self, file_path: str):
        """
        Синхронная загрузка одного файла в папку self.folder_id.
        Используется из пула потоков.
        """
        file_name = os.path.basename(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

        file_metadata = {
            'name': file_name,
            'parents': [self.folder_id]  # Используем папку по умолчанию
        }

        media = MediaFileUpload(file_path, mimetype=mime_type)

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get("id")

    async def upload_files(self, file_paths: list[str]):
        """
        Асинхронная загрузка всех файлов в self.folder_id.
        """
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            tasks = [
                loop.run_in_executor(executor, self._upload_file_sync, path)
                for path in file_paths
            ]
            uploaded_ids = await asyncio.gather(*tasks)
            return uploaded_ids


uploader = GoogleDriveUploader(config.google_folder_id)
