from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from handlers.cmd_show import PaginationState
from keyboards.show_dumps_kb import build_dumps_keyboard_with_pagination

router = Router()


@router.callback_query(PaginationState.viewing_list, F.data.in_(["prev_page", "next_page"]))
async def handle_page_change(callback: types.CallbackQuery, state: FSMContext):
    """Обработка переключения страниц"""
    data = await state.get_data()
    current_page = data.get("current_page", 0)

    if callback.data == "prev_page":
        new_page = current_page - 1
    else:
        new_page = current_page + 1

    # Обновляем состояние
    await state.update_data(current_page=new_page)

    # Редактируем сообщение с новой клавиатурой
    await callback.message.edit_text(
        "Список элементов:",
        reply_markup=await build_dumps_keyboard_with_pagination(new_page)
    )
    await callback.answer()


@router.callback_query(PaginationState.viewing_list, F.data.startswith("item_"))
async def handle_item_selection(callback: types.CallbackQuery):
    """Обработка выбора элемента"""
    item_idx = int(callback.data.split("_")[1])
    await callback.answer(f"Вы выбрали: {item_idx}", show_alert=True)