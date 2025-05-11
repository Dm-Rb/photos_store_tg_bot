from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def edit_keyboard(dump_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить описание", callback_data=f"edit_description_dumpid;{str(dump_id)}")
    builder.button(text="➕ Добавить фотографии", callback_data=f"edit_photos_dumpid;{str(dump_id)}")
    builder.adjust(1)

    return builder.as_markup()


async def save_cancel_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/save 💾"),
                KeyboardButton(text="/cancel ❌"),
            ]
        ],
        resize_keyboard=True
    )
    return kb
