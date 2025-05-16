from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from text.messages import msg_edit_keyboard


async def edit_keyboard(dump_id):
    builder = InlineKeyboardBuilder()
    builder.button(text=msg_edit_keyboard['add_description'], callback_data=f"descr_edit_id:{str(dump_id)}")
    builder.button(text=msg_edit_keyboard['add_files'], callback_data=f"file_edit_id:{str(dump_id)}"),
    builder.button(text=msg_edit_keyboard['del_dump'], callback_data=f"del_dump_id:{str(dump_id)}")
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
