from services.archiving_files import archiving_files_main
from services.google_drive import google_drive
import asyncio
import os
from config import config
from datetime import datetime
from services.google_drive import GoogleDriveUploader
from services.archiving_files import extract_zip_from_memory


async def backup_to_gdrive():

    # Create archives
    result_dict = await archiving_files_main()  # -> {'zip_file_list': [], 'files_list':[] or None
    if not result_dict:
        return

    # Upload archives to Google Drive
    await google_drive.upload_files(result_dict['zip_file_list'])

    # Delete zip files
    for file_ in result_dict['zip_file_list']:
        try:
            os.remove(file_)
        except Exception as e:
            continue

    # Deleting remaining files (media)
    for file_ in result_dict['files_list']:
        try:
            os.remove(file_)
        except Exception as e:
            continue


async def scheduled_backup():
    """Функция бэкапа в Google Drive"""
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == config.BACKUP_TIME:  # Время из конфига (например, "03:00")
            await backup_to_gdrive()
            await asyncio.sleep(60)  # Ждём минуту, чтобы не спамить
        await asyncio.sleep(30)  # Проверяем каждые 30 секунд


def sync_get_archives_extract_files(catalog_id):
    mediafile_list = []
    google_drive__ = GoogleDriveUploader(config.google_folder_id)
    archives_list = google_drive__.get_dump_archives(catalog_id)

    for archive_item in archives_list:
        archive_data = extract_zip_from_memory(archive_item[1], "kal_i-mocha")
        mediafile_list.extend(archive_data)

    return mediafile_list


