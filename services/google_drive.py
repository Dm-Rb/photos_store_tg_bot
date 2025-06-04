import os
import mimetypes
from config import config
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request, AuthorizedSession
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
import io
import asyncio


# pip install --upgrade google-api-python-client google-auth google-auth-oauthlib requests
class GoogleDriveUploader:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']

    def __init__(self, folder_id: str = None, credentials_path: str = config.GOOGLE_CREDENTIALS_FILE,
                 token_path: str = 'token.json'):

        self.folder_id = folder_id
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = self._authenticate()
        self.session = AuthorizedSession(self.creds)
        self.service = build(
            'drive', 'v3',
            credentials=self.creds
        )

    def _request_builder(self, *args, **kwargs):
        from googleapiclient.http import HttpRequest
        return HttpRequest(self.session, *args, **kwargs)

    def _authenticate(self):
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

    def _upload_file_sync(self, file_path: str, folder_enable: bool = True):
        # arg: folder_enable is flag. True - file save to a specific Google Drive folder
        # False -  back to Drive root if unspecified

        file_name = os.path.basename(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

        file_metadata = {'name': file_name}
        if self.folder_id and folder_enable:
            file_metadata['parents'] = [self.folder_id]

        chunk_size = 10 * 1024 * 1024  # 10MB
        with open(file_path, 'rb') as f:
            media = MediaIoBaseUpload(f, mimetype=mime_type, chunksize=chunk_size, resumable=True)
            request = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"Upload progress: {int(status.progress() * 100)}%")

        return response.get("id")

    async def upload_files(self, file_paths: list[str], folder_enable=True):
        """
        Обертка для загрузски списка файлов. Тут можно было реализовать параллельную вгрузку через asyncio.gather
        Однако google client выёбывается время от времени и руинит код. Именно поэтому загружаем последовательно
        в выделенном потоке
        """
        for file_path in file_paths:
            await asyncio.to_thread(self._upload_file_sync, file_path, folder_enable)

    def _get_list_files_sync(self) -> list[dict]:
        """
        Return a list of all files on Google Drive with their names and IDs
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
