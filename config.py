import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    PASSPHRASE = os.getenv("PASSPHRASE")
    GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
    google_folder_id = os.getenv("google_drive_folder_id")
    BACKUP_TIME = os.getenv("BACKUP_TIME")  # Format HH:MM
    clear_local_disk_after_backup = int(os.getenv("clear_local_disk_after_backup"))  # 1 or 0
    backup_files_on_google_drive = int(os.getenv("backup_files_on_google_drive"))  # 1 or 0

    def __init__(self):
        self.FILES_DIR_UPLOAD = 'files_upload'  # Tmp dir for files
        Path(self.FILES_DIR_UPLOAD).mkdir(exist_ok=True)


config = Config()




