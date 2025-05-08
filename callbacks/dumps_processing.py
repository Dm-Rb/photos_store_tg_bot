from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from handlers.cmd_show import PaginationState
from keyboards.show_dumps_kb import build_dumps_keyboard_with_pagination
from services.database import dumps_db, files_db

router = Router()


@router.callback_query(PaginationState.viewing_list, F.data.in_(["prev_page", "next_page"]))
async def handle_page_change(callback: types.CallbackQuery, state: FSMContext):
    """Обработка переключения страниц"""
    data = await state.get_data()
    current_page = data.get("current_page", 0)
    photo_dumps_tittles = data.get("photo_dumps_tittles", [])
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


@router.callback_query(PaginationState.viewing_list, F.data.startswith("dumpid_"))
async def handle_item_selection(callback: types.CallbackQuery):
    """Обработка выбора элемента"""
    print(callback.data)
    dump_id = callback.data.split("_")[1]

    # Отправляем тектовое сообщение с описанием
    _, title, description = dumps_db.select_row_by_id(int(dump_id))
    await callback.message.answer(text=f"{title}\n{description}")

    # Отправляем группу файлов
    photos_list = files_db.select_rows_by_id(dump_id)
    start_i = 0
    step = 10
    for i in range(0, len(photos_list), 10):
        items = photos_list[start_i: start_i + step]
        media_group = [
            types.InputMediaPhoto(media=item['telegram_file_id']) for item in items
        ]
        start_i += step
        await callback.message.answer_media_group(media=media_group)
    # Подтверждаем обработку колбэка (убираем "часики")
    await callback.answer()