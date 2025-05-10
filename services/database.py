import aiosqlite
import sqlite3
from pathlib import Path
import datetime


class DataBase:

    def __init__(self, db_name: str = 'data.db'):
        self.db_path = Path(__file__).parent.parent / db_name

        # Создаём файл БД, если его нет (необязательно, т.к. SQLite создаст его автоматически)
        self.db_path.parent.mkdir(exist_ok=True)  # Создаёт папки, если их нет
        self.db_path.touch(exist_ok=True)  # Создаёт файл, если его нет
        self.__create_table__users()
        self.__create_table__dumps()
        self.__create_table__photos()

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

    def __create_table__dumps(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'''
                CREATE TABLE IF NOT EXISTS dumps (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT
                )
                '''
            )
            conn.commit()

    def __create_table__photos(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f'''
                CREATE TABLE IF NOT EXISTS photos (
                    photo_name TEXT NOT NULL,                    
                    telegram_file_id INTEGER,
                    dump_id INTEGER
                )
                '''
            )
            conn.commit()


class Users(DataBase):

    def __init__(self, db_path="data.db"):
        super().__init__(db_path)  # Вызов родительского __init__
        self.cache: dict = self.get_users_cache()

    def init(self):
        pass

    def select_all(self):
        with sqlite3.connect(self.db_path) as conn:
            response = conn.execute(
                'SELECT * FROM users'
            ).fetchall()

        return response

    def insert(self, user_id: int, user_permission: int = 1):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO users (user_id, user_permission) VALUES(?, ?)',
                (user_id, user_permission, )
            )
        self.cache[user_id] = user_permission
        return

    def get_users_cache(self):
        data = self.select_all()
        if data:
            cash = {key: value for key, value in data}
            return cash
        else:
            return dict({})


class PhotoDumps(DataBase):
    """
    Класс представляет из себя название группы фотографий
    """
    def __init__(self, db_path="data.db"):
        super().__init__(db_path)  # Вызов родительского __init__
        self.cache_list: list = self.get_dumps_cache()

    def select_all(self):
        with sqlite3.connect(self.db_path) as conn:
            response = conn.execute(
                'SELECT * FROM dumps'
            ).fetchall()

        return response

    def get_dumps_cache(self):
        data = self.select_all()
        if data:
            cash = [{'title': item[1], 'id': item[0]} for item in data]
            return cash
        else:
            return []

    def insert(self, title: str, description: str = 1):
        if len(title) >= 64:
            title = title[:64]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'INSERT INTO dumps (title, description) VALUES(?, ?)',
                (title, description,)
            )
            last_id = cursor.lastrowid
        self.cache_list.append({'title': title, 'id': last_id})  # Добавляем новую запись в рабочий список
        return last_id
    
    def select_row_by_id(self, id_):
        with sqlite3.connect(self.db_path) as conn:
            response = conn.execute(
                'SELECT * FROM dumps WHERE id=?',
                (id_, )
            ).fetchone()

        return response

    def update_description_by_id(self, id_, text):
        with sqlite3.connect(self.db_path) as conn:
            sql = """
                UPDATE dumps 
                SET description = COALESCE(description, '') || '***' || ?
                WHERE id = ?;
            """
            # Передаём параметры в правильном порядке: text идёт первым, затем id_
            conn.execute(sql, (text, id_))
            conn.commit()







class PhotoFiles(DataBase):
    def __init__(self, db_path="data.db"):
        super().__init__(db_path)  # Вызов родительского __init__
        self.cache = None

    def insert(self, photo_name, telegram_file_id, dump_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO photos (photo_name, telegram_file_id, dump_id) VALUES(?, ?, ?)',
                (photo_name, telegram_file_id, dump_id, )
            )

    def select_rows_by_id(self, dump_id):
        with sqlite3.connect(self.db_path) as conn:
            response = conn.execute(
                'SELECT * FROM photos WHERE dump_id = ?',
                (dump_id, )
            ).fetchall()
        if response:
            return [{'photo_name': item[0], 'telegram_file_id': item[1]} for item in response]
        return response


users_db = Users()
dumps_db = PhotoDumps()
files_db = PhotoFiles()


# dumps_db.update_description_by_id(4, 'jkjkjk jjjjdvdf')
