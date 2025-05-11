from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from services.database import catalogs_db
from aiogram.utils.keyboard import InlineKeyboardBuilder


ITEMS_PER_PAGE = 10  # Количество элементов на странице


async def build_dumps_keyboard_with_pagination(page: int = 0, edit=False) -> InlineKeyboardMarkup:
    """Строит клавиатуру с пагинацией"""
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_page_items = catalogs_db.cache_list[start_idx:end_idx]

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки элементов
    for item in current_page_items:
        button_name = f"🗂 {item['title']}"
        if len(button_name) > 40:
            button_name = f"{button_name[:48]}..."
        if edit:
            builder.button(text=button_name, callback_data=f"editdumpid_{str(item['id'])}")
        else:
            builder.button(text=button_name, callback_data=f"dumpid_{str(item['id'])}")

    # Добавляем кнопки навигации
    navigation_buttons = []

    # Кнопка "Назад" (если не на первой странице)
    if page > 0:
        navigation_buttons.append(
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_page")
        )

    # Кнопка "Вперёд" (если не на последней странице)
    if end_idx < len(catalogs_db.cache_list):
        navigation_buttons.append(
            types.InlineKeyboardButton(text="Далей ➡️", callback_data="next_page")
        )

    # Располагаем элементы
    builder.adjust(1)  # По одному элементу в строке
    if navigation_buttons:  # Добавляем навигацию только если есть кнопки
        builder.row(*navigation_buttons)

    return builder.as_markup()