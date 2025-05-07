from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


ITEMS_PER_PAGE = 10  # Количество элементов на странице


async def build_dumps_keyboard_with_pagination(photo_dumps:list, page: int = 0) -> InlineKeyboardMarkup:
    """Строит клавиатуру с пагинацией"""
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_page_items = photo_dumps[start_idx:end_idx]

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки элементов
    for item in current_page_items:
        builder.button(text=item, callback_data=f"item_{photo_dumps.index(item)}")

    # Добавляем кнопки навигации
    navigation_buttons = []

    # Кнопка "Назад" (если не на первой странице)
    if page > 0:
        navigation_buttons.append(
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_page")
        )

    # Кнопка "Вперёд" (если не на последней странице)
    if end_idx < len(photo_dumps):
        navigation_buttons.append(
            types.InlineKeyboardButton(text="Вперёд ➡️", callback_data="next_page")
        )

    # Располагаем элементы
    builder.adjust(1)  # По одному элементу в строке
    if navigation_buttons:  # Добавляем навигацию только если есть кнопки
        builder.row(*navigation_buttons)

    return builder.as_markup()

