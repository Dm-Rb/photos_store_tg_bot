from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from services.database import users_db, dumps_db
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboards.show_dumps_kb import build_dumps_keyboard_with_pagination


router = Router()


class PaginationState(StatesGroup):
    viewing_list = State()  # Состояние просмотра списка


@router.message(Command("show"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /show - инициализация пагинации"""
    await state.set_state(PaginationState.viewing_list)
    await state.update_data(current_page=0)  # Начинаем с первой страницы
    photo_dumps_tittles = list(dumps_db.cache.keys())
    await state.update_data(current_page=0, photo_dumps_tittles=photo_dumps_tittles)
    await message.answer(
        "Список дампов:",
        reply_markup=await build_dumps_keyboard_with_pagination(photo_dumps_tittles, 0)
    )


