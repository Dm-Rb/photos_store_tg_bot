from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.database import dumps_db

ITEMS_PER_PAGE = 10  # Количество элементов на странице


async def build_dumps_keyboard_with_pagination(page: int = 0) -> InlineKeyboardMarkup:
    """Строит клавиатуру с пагинацией"""
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    # photo_dumps = dumps_db.cache_list
    current_page_items = dumps_db.cache_list[start_idx:end_idx]

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки элементов
    for item in current_page_items:
        button_name = item['title']
        if len(button_name) > 38:
            button_name = f"{button_name[:34]}..."
        builder.button(text=button_name, callback_data=f"dumpid_{str(item['id'])}")

    # Добавляем кнопки навигации
    navigation_buttons = []

    # Кнопка "Назад" (если не на первой странице)
    if page > 0:
        navigation_buttons.append(
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_page")
        )

    # Кнопка "Вперёд" (если не на последней странице)
    if end_idx < len(dumps_db.cache_list):
        navigation_buttons.append(
            types.InlineKeyboardButton(text="Вперёд ➡️", callback_data="next_page")
        )

    # Располагаем элементы
    builder.adjust(1)  # По одному элементу в строке
    if navigation_buttons:  # Добавляем навигацию только если есть кнопки
        builder.row(*navigation_buttons)

    return builder.as_markup()
