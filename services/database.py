import aiosqlite
from pathlib import Path
import sqlite3


class DataBase:

    def __init__(self, db_name: str = 'data.db'):
        self.db_path = Path(__file__).parent.parent / db_name

        # Создаём файл БД, если его нет (необязательно, т.к. SQLite создаст его автоматически)
        self.db_path.parent.mkdir(exist_ok=True)  # Создаёт папки, если их нет
        self.db_path.touch(exist_ok=True)  # Создаёт файл, если его нет
        self.__create_table__users()
        self.__create_table__catalogs()
        self.__create_table__files()

    def __create_table__users(self):
        """
        user_id: str - telegram user id,
        user_permission: int - 1 or 0 / 1 - permission to write and edit, 2 - only read, 3 - ban

        """

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER UNIQUE NOT NULL,
                    user_permission INTEGER DEFAULT 1
                )
                '''
            )
            conn.commit()

    def __create_table__catalogs(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'''
                CREATE TABLE IF NOT EXISTS catalogs (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    datetime TEXT
                )
                '''
            )
            conn.commit()

    def __create_table__files(self):
        # file_type - constanta. 1 - mediafile, 2 - document
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'''
                CREATE TABLE IF NOT EXISTS files (
                    file_name TEXT NOT NULL,                    
                    telegram_file_id INTEGER,                                        
                    catalog_id INTEGER,
                    file_type INTEGER
                )
                '''
            )
            conn.commit()


class Users(DataBase):

    def __init__(self, db_path="data.db"):
        super().__init__(db_path)  # Вызов родительского __init__
        self.cache: dict = self.get_users_cache()

    def get_users_cache(self):
        with sqlite3.connect(self.db_path) as conn:
            response = conn.execute(
                'SELECT * FROM users'
            ).fetchall()

        if response:
            cash = {key: value for key, value in response}
            return cash
        else:
            return dict({})

    async def select_all(self):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute('SELECT * FROM users') as cursor:
                return await cursor.fetchall()

    async def insert(self, user_id: int, user_permission: int = 1):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                'INSERT INTO users (user_id, user_permission) VALUES(?, ?)',
                (user_id, user_permission)
            )
            await conn.commit()
        self.cache[user_id] = user_permission

    async def delete(self, user_id):
        async with aiosqlite.connect(self.db_path) as conn:
            try:
                await conn.execute(
                    'DELETE FROM users WHERE user_id=?',
                    (user_id,)
                )
                await conn.commit()
            except Exception as ex_:
                return


class Catalogs(DataBase):
    """
    Класс представляет из себя название группы фотографий
    """

    def __init__(self, db_path="data.db"):
        super().__init__(db_path)  # Вызов родительского __init__
        self.cache_list: list = self.get_catalogs_cache()

    def get_catalogs_cache(self):
        with sqlite3.connect(self.db_path) as conn:
            response = conn.execute(
                'SELECT * FROM catalogs ORDER BY datetime DESC'
            ).fetchall()
        if response:
            cash = [{'title': item[1], 'id': item[0]} for item in response]
            return cash
        else:
            return []

    async def select_all(self):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute('SELECT * FROM catalogs') as cursor:
                return await cursor.fetchall()

    async def insert(self, title: str, description: str = None, datetime: str = None):
        if len(title) >= 64:
            title = title[:64]
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                'INSERT INTO catalogs (title, description, datetime) VALUES(?, ?, ?)',
                (title, description, datetime)
            )
            last_id = cursor.lastrowid
            await conn.commit()
        self.cache_list = [{'title': title, 'id': last_id}] + self.cache_list # Добавляем новую запись в начало списока
        return last_id

    async def select_row_by_id(self, id_):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                    'SELECT * FROM catalogs WHERE id=?',
                    (id_,)
            ) as cursor:
                return await cursor.fetchone()

    async def update_description_by_id(self, id_, text):
        async with aiosqlite.connect(self.db_path) as conn:
            sql = """
                UPDATE catalogs 
                SET description = COALESCE(description, '') || '***' || ?
                WHERE id = ?;
            """
            await conn.execute(sql, (text, id_))
            await conn.commit()

    async def update_datetime_by_id(self, id_, datetime):
        async with aiosqlite.connect(self.db_path) as conn:
            sql = """
                UPDATE catalogs 
                SET datetime = ?
                WHERE id = ?;
            """
            await conn.execute(sql, (datetime, id_))
            await conn.commit()
        self.cache_list: list = self.get_catalogs_cache()

    async def delete_row_by_id(self, id_):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                'DELETE FROM catalogs WHERE id=?',
                (id_,)
            )
            # Delete from self.cache_list
            for i, item in enumerate(self.cache_list):
                if int(item["id"]) == int(id_):
                    self.cache_list.pop(i)
                    break
            await conn.commit()


class PhotoFiles(DataBase):
    def __init__(self, db_path="data.db"):
        super().__init__(db_path)  # Вызов родительского __init__

    async def insert(self, file_name, telegram_file_id, catalog_id):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                'INSERT INTO files (file_name, telegram_file_id, catalog_id) VALUES(?, ?, ?)',
                (file_name, telegram_file_id, catalog_id)
            )
            await conn.commit()

    async def select_rows_by_id(self, catalog_id):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                    'SELECT file_name, telegram_file_id FROM files WHERE catalog_id = ?',
                    (catalog_id,)
            ) as cursor:
                response = await cursor.fetchall()
        if response:
            return [{'file_name': item[0], 'telegram_file_id': item[1]} for item in response]
        return response

    async def delete_rows_by_catalog_id(self, catalog_id):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                'DELETE FROM files WHERE catalog_id=?',
                (catalog_id,)
            )
            await conn.commit()

    async def select_catalogid_by_filename(self, file_name):
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(
                'SELECT catalog_id FROM files WHERE file_name = ?',
                (file_name,)
            ) as cursor:
                response = await cursor.fetchone()
        if response:
            return response[0]



users_db = Users()
catalogs_db = Catalogs()
files_db = PhotoFiles()

