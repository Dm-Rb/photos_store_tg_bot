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


class Users(DataBase):

    def __init__(self, db_path="data.db"):
        super().__init__(db_path)  # Вызов родительского __init__
        self.cache = self.get_users_cache()

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
        return

    def get_users_cache(self):
        data = self.select_all()
        if data:
            cash = {key: value for key, value in data}
            return cash
        else:
            return dict({})


users_db = Users()

