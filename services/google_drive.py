import mimetypes
import asyncio
from concurrent.futures import ThreadPoolExecutor
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from config import config
from googleapiclient.http import MediaIoBaseDownload
import io
import os


class GoogleDriveUploader:
    """
    Класс для загрузки файлов на Google Drive.
    Хранит авторизацию и целевую папку загрузки (folder_id).
    """

    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(
        self,
        folder_id: str = None,
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
        }
        if self.folder_id:
            file_metadata['parents'] = [self.folder_id]  # Используем папку по умолчанию

        media = MediaFileUpload(file_path, mimetype=mime_type)

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get("id")

    async def upload_files(self, file_paths: list[str]):
        """
        Асинхронная загрузка всех файлов в self.folder_id с таймаутом и ограничением потоков.
        """
        max_workers: int = 4
        timeout: int = 3000
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # Ограничиваем потоки
            tasks = []
            for path in file_paths:
                # Добавляем таймаут для каждой задачи
                task = asyncio.wait_for(
                    loop.run_in_executor(executor, self._upload_file_sync, path),
                    timeout=timeout
                )
                tasks.append(task)

            try:
                uploaded_ids = await asyncio.gather(*tasks, return_exceptions=True)
                # Фильтруем успешные загрузки
                return [id_ for id_ in uploaded_ids if not isinstance(id_, Exception)]
            except Exception as e:
                print(f"Upload failed: {e}")
                return []

    def _get_list_files_sync(self) -> list[dict]:
        """
        Синхронно возвращает список всех файлов на Google Диске с их именами и ID.
        """
        files = []
        page_token = None

        while True:
            response = self.service.files().list(
                q="trashed = false",  # Исключаем удалённые
                spaces='drive',
                fields='nextPageToken, files(id, name)',
                pageToken=page_token
            ).execute()

            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)

            if not page_token:
                break
        return files  # files = [{'id': str, 'name': str}, ...]

    def download_file_by_id_to_memory(self, file_id: str) -> tuple[str, io.BytesIO] | None:
        """
        Скачивает файл из Google Drive в оперативную память.
        Возвращает кортеж (имя_файла, io.BytesIO), либо None при ошибке.
        """
        try:
            # Получаем имя файла
            file_metadata = self.service.files().get(fileId=file_id, fields='name').execute()
            file_name = file_metadata.get('name')

            # Скачиваем файл в память
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)  # Обязательно сбросить указатель в начало
            return file_name, fh

        except Exception as e:
            print(f"Ошибка при скачивании файла {file_id}: {e}")
            return None

    def get_dump_archives(self, catalog_id):
        list_files = self._get_list_files_sync()
        # Filtering
        list_files = [i for i in list_files if i['name'].startswith(f"{str(catalog_id)}_")]
        result = []
        for zip_file in list_files:
            r = self.download_file_by_id_to_memory(zip_file['id'])
            result.append(r)
        return result


google_drive = GoogleDriveUploader(config.google_folder_id)
google_drive_db = GoogleDriveUploader()
