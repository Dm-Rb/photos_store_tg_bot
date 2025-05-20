import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    PASSPHRASE = os.getenv("PASSPHRASE")
    google_folder_id = os.getenv("google_drive_folder_id")
    BACKUP_TIME = os.getenv("BACKUP_TIME")  # Время бэкапа (формат HH:MM)


# екземпляр конфигурации для импорта и использования
config = Config()

FILES_DIR_UPLOAD = 'files_upload'  # Tmp-dir for photos, video and archives
Path(FILES_DIR_UPLOAD).mkdir(exist_ok=True)
FILES_DIR_DOWNLOAD = 'files_download'
Path(FILES_DIR_DOWNLOAD).mkdir(exist_ok=True)
