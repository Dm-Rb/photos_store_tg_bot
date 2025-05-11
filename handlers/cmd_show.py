from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.catalog_kb import build_dumps_keyboard_with_pagination
from text.handlers_txt import msg_cmd_show
from services.database import users_db


router = Router()


class PaginationState(StatesGroup):
    viewing_list = State()  # Состояние просмотра списка


@router.message(Command("show"))
async def cmd_show(message: Message, state: FSMContext):
    """Обработка команды /show - инициализация пагинации"""

    if not users_db.cache.get(message.from_user.id, None):
        return
    await state.set_state(PaginationState.viewing_list)
    await state.update_data(current_page=0)  # Начинаем с первой страницы
    await message.answer(
        text=msg_cmd_show,
        parse_mode="HTML",
        reply_markup=await build_dumps_keyboard_with_pagination(0)
    )
