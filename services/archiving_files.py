import os
import asyncio
import time
from typing import Dict, List, Optional
import pyzipper
from slugify import slugify
from config import FILES_DIR_UPLOAD, config
from services.database import files_db, catalogs_db
import io


async def grouping_files(dir_path: str) -> Dict[int, List[str]]:
    """Асинхронно группирует файлы по catalog_id."""
    groups: Dict[int, List[str]] = {}

    # Асинхронно получаем catalog_id для каждого файла
    catalog_ids = []
    for file_name in os.listdir(dir_path):
        catalog_id = await files_db.select_catalogid_by_filename(file_name)
        catalog_ids.append(catalog_id)

    # Группируем результаты
    for file_name, catalog_id in zip(os.listdir(dir_path), catalog_ids):
        if catalog_id is not None:
            if catalog_id not in groups:
                groups[catalog_id] = []
            groups[catalog_id].append(file_name)

    return groups


async def create_encrypted_zip(file_list: List[str], password: str, archive_path: str) -> None:
    """
    Асинхронно создаёт AES-256 зашифрованный ZIP-архив.
    Использует отдельный поток для операций с файлами.
    """
    password_bytes = password.encode('utf-8')

    def _sync_create_zip():
        with pyzipper.AESZipFile(
                archive_path,
                'w',
                compression=pyzipper.ZIP_LZMA,
                encryption=pyzipper.WZ_AES
        ) as zf:
            zf.setpassword(password_bytes)
            zf.setencryption(pyzipper.WZ_AES, nbits=256)

            for file_path in file_list:
                arcname = os.path.basename(file_path)
                zf.write(file_path, arcname=arcname)

    # Запускаем синхронную операцию в отдельном потоке
    await asyncio.to_thread(_sync_create_zip)


async def archive_catalog_files(catalog_id: int, file_names: List[str]) -> Optional[str]:
    """Архивирует файлы одного каталога и возвращает путь к архиву."""
    try:
        t = int(time.time())
        catalog_title = next(
            (item['title'] for item in catalogs_db.cache_list
             if str(item['id']) == str(catalog_id)),
            None
        )

        if not catalog_title:
            return None

        safe_title = slugify(catalog_title)
        zip_name = f"{catalog_id}_{safe_title}-{t}.zip"
        zip_path = os.path.join(FILES_DIR_UPLOAD, zip_name)

        file_paths = [os.path.join(FILES_DIR_UPLOAD, name) for name in file_names]
        await create_encrypted_zip(file_paths, config.PASSPHRASE, zip_path)

        return zip_path
    except Exception as e:
        print(f"Error archiving catalog {catalog_id}: {e}")
        return None


async def archiving_files_main() -> Dict[str, List[str]]:
    """Основная асинхронная функция для архивирования файлов."""
    groups = await grouping_files(FILES_DIR_UPLOAD)
    if not groups:
        return {"zip_file_list": [], "files_list": []}

    # Создаем задачи для параллельного архивирования
    tasks = []
    for catalog_id, file_names in groups.items():
        tasks.append(archive_catalog_files(catalog_id, file_names))

    zip_files = await asyncio.gather(*tasks)

    # Фильтруем None результаты и собираем список файлов
    zip_file_list = [zf for zf in zip_files if zf is not None]
    files_list = [
        os.path.join(FILES_DIR_UPLOAD, fname)
        for group in groups.values()
        for fname in group
    ]

    return {"zip_file_list": zip_file_list, "files_list": files_list}


def extract_zip_from_memory(zip_stream: io.BytesIO, password: str) -> list[dict]:
    """
    Извлекает файлы из зашифрованного ZIP-архива, переданного как io.BytesIO.
    Возвращает словарь: {имя_файла: io.BytesIO}
    """
    # Сброс указателя на начало архива
    zip_stream.seek(0)
    result = []
    with pyzipper.AESZipFile(zip_stream, 'r') as zf:
        zf.setpassword(password.encode())

        for file_name in zf.namelist():
            if not file_name.endswith("/"):  # Пропускаем директории
                file_bytes = zf.read(file_name)
                result.append({'file_name': file_name, 'bytes': io.BytesIO(file_bytes)})
    return result
