from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.database import dumps_db


async def build_edit_keyboard(dump_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить описание", callback_data=f"edit_description_dumpid;{str(dump_id)}")
    builder.button(text="➕ Добавить фотографии", callback_data=f"edit_photos_dumpid;{str(dump_id)}")
    builder.adjust(1)

    return builder.as_markup()