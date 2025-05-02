import os
import hashlib


def generate_hash_name(input_string: str, length: int = 8) -> str:
    """
    Генерирует короткий хеш (по умолчанию 8 символов) из строки.
    :param input_string: Входная строка (например, file_id)
    :param length: Длина хеша (максимум 32 для md5)
    :return: Хеш (например, 'a1b2c3d4')
    """
    hash_object = hashlib.md5(input_string.encode())
    return hash_object.hexdigest()[:length]
