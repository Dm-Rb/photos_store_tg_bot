import asyncio
import os
from services.archiving_files import archiver, delete_file
from services.google_drive import google_drive, google_drive_db
from config import config
from datetime import datetime
from services.google_drive import GoogleDriveUploader


async def backup_to_gdrive():

    # Create archives
    result_dict = await archiver.archiving_files_processor()  # -> {'zip_file_list': [], 'files_list':[] or None
    if not result_dict:
        return
    if not config.backup_files_on_google_drive:
        return

    # Upload archives to Google Drive
    if result_dict['zip_file_list']:
        await google_drive.upload_files(result_dict['zip_file_list'], True)  # archives to folder of GD
        await google_drive.upload_files(['data.db'], False)  # database file to root of GD

    # Deleting remaining files (media)
    if result_dict.get('files_list', None):
        tasks = [delete_file(filename) for filename in result_dict['files_list']]
        await asyncio.gather(*tasks)

    # Delete zip files
    if config.clear_local_disk_after_backup:
        for file_ in result_dict['zip_file_list']:
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
        archive_data = archiver.extract_zip_from_memory(archive_item[1], config.PASSPHRASE)
        mediafile_list.extend(archive_data)

    return mediafile_list


