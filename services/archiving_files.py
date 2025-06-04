import os
import asyncio
import time
from typing import Dict, List, Optional
import pyzipper
from slugify import slugify
from config import config
from services.database import files_db, catalogs_db
import aiofiles.os as aio_os
import io


class ArchivingFiles:

    """This class includes methods for zipping and unzipping files"""

    @staticmethod
    async def _grouping_files(dir_path: str) -> Dict[int, List[str]]:
        """Asynchronously groups files by catalog_id"""

        groups: Dict[int, List[str]] = {}

        # Get catalog_id for any file
        catalog_ids = []
        for file_name in os.listdir(dir_path):
            catalog_id = await files_db.select_catalogid_by_filename(file_name)
            catalog_ids.append(catalog_id)

        # Grouping results
        for file_name, catalog_id in zip(os.listdir(dir_path), catalog_ids):
            if catalog_id is not None:
                if catalog_id not in groups:
                    groups[catalog_id] = []
                groups[catalog_id].append(file_name)

        return groups

    @staticmethod
    async def _create_encrypted_zip(file_list: List[str], password: str, archive_path: str) -> None:
        """
        Asynchronously generates an AES-256 encrypted ZIP archive.
        File operations are performed in a separate thread.
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

        # Run sync foo in separate thread
        await asyncio.to_thread(_sync_create_zip)

    async def _archive_catalog_files(self, catalog_id: int, file_names: List[str]) -> Optional[str] or None:
        """"Archives files for a choiced catalog and returns the path to the created archive"""

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
            zip_path = os.path.join(config.FILES_DIR_UPLOAD, zip_name)

            file_paths = [os.path.join(config.FILES_DIR_UPLOAD, name) for name in file_names]
            await self._create_encrypted_zip(file_paths, config.PASSPHRASE, zip_path)
            return zip_path

        except Exception as e:
            print(f"Error archiving catalog {catalog_id}: {e}")
            return None

    async def archiving_files_processor(self) -> Dict[str, List[str]]:
        """Main async method for archives files. This is a wrapper that gets called externally"""
        groups = await self._grouping_files(config.FILES_DIR_UPLOAD)
        if not groups:
            return {"zip_file_list": [], "files_list": []}

        # Create tasks for parallel archiving
        tasks = []
        for catalog_id, file_names in groups.items():
            tasks.append(self._archive_catalog_files(catalog_id, file_names))

        zip_files = await asyncio.gather(*tasks)

        # Filtering None results and collect list of files
        zip_file_list = [zf for zf in zip_files if zf is not None]
        files_list = [
            os.path.join(config.FILES_DIR_UPLOAD, fname)
            for group in groups.values()
            for fname in group
        ]

        return {"zip_file_list": zip_file_list, "files_list": files_list}

    @staticmethod
    def extract_zip_from_memory(zip_stream: io.BytesIO, password: str) -> list[dict]:
        """
        Extracts files from an AES-encrypted ZIP archive (provided as io.BytesIO).
        Returns:
            Dict[str, io.BytesIO]: A dictionary mapping filenames to their binary data streams.
        """
        # Returns the file pointer to the beginning of the archive
        zip_stream.seek(0)
        result = []
        with pyzipper.AESZipFile(zip_stream, 'r') as zf:
            zf.setpassword(password.encode())

            for file_name in zf.namelist():
                if not file_name.endswith("/"):  # Пропускаем директории
                    file_bytes = zf.read(file_name)
                    result.append({'file_name': file_name, 'bytes': io.BytesIO(file_bytes)})
        # -> [{'file_name': str, 'bytes': binary}, {}, ...]
        return result


async def delete_file(filename: str) -> None:
    """Delete file async"""
    try:
        await aio_os.remove(filename)
    except Exception as e:
        print(f"Error delete file {filename}: {e}")
        return

archiver = ArchivingFiles()
