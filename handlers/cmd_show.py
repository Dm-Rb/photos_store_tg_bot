from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.show_dumps_kb import build_dumps_keyboard_with_pagination
from text.handlers_txt import msg_cmd_show


router = Router()


class PaginationState(StatesGroup):
    viewing_list = State()  # Состояние просмотра списка


@router.message(Command("show"))
async def cmd_show(message: Message, state: FSMContext):
    """Обработка команды /show - инициализация пагинации"""
    await state.set_state(PaginationState.viewing_list)
    await state.update_data(current_page=0) # Начинаем с первой страницы
    await message.answer(
        text=msg_cmd_show,
        reply_markup=await build_dumps_keyboard_with_pagination(0)
    )
