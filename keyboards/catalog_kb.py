from aiogram import types
from aiogram.types import InlineKeyboardMarkup
from services.database import catalogs_db
from aiogram.utils.keyboard import InlineKeyboardBuilder


ITEMS_PER_PAGE = 10  # Keyboard button limit on "page"


async def build_dumps_keyboard_with_pagination(page: int = 0, edit=False) -> InlineKeyboardMarkup:
    """Build inline keyboard with pagination"""
    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_page_items = catalogs_db.cache_list[start_idx:end_idx]

    builder = InlineKeyboardBuilder()

    # Add buttons
    for item in current_page_items:
        button_name = f"🗂 {item['title']}"
        if len(button_name) > 40:
            button_name = f"{button_name[:48]}..."
        if edit:
            builder.button(text=button_name, callback_data=f"edit:{str(item['id'])}")
        else:
            builder.button(text=button_name, callback_data=f"show:{str(item['id'])}")

    navigation_buttons = []

    # Button "Back" (if current page not first)
    if page > 0:
        navigation_buttons.append(
            types.InlineKeyboardButton(text="⬅️ Назад", callback_data="prev_page")
        )

    # Button "Next" (if current page not last)
    if end_idx < len(catalogs_db.cache_list):
        navigation_buttons.append(
            types.InlineKeyboardButton(text="Далей ➡️", callback_data="next_page")
        )

    # Arrange elements
    builder.adjust(1)  # One element per row
    if navigation_buttons:
        builder.row(*navigation_buttons)
    return builder.as_markup()
