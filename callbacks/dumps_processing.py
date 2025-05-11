from aiogram import types, F, Router
from handlers.cmd_show import PaginationState
from keyboards.catalog_kb import build_dumps_keyboard_with_pagination
import keyboards.keyboards as kb
from services.database import catalogs_db, files_db
from text.handlers_txt import msg_handle_item_selection
from handlers.cmd_edit import EditState
from aiogram.fsm.context import FSMContext
from text.handlers_txt import msg_process_description, msgs_process_title
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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


@router.callback_query(PaginationState.viewing_list, F.data.startswith("dumpid_"))
async def handle_show_dump(callback: types.CallbackQuery):
    """Обработка выбора элемента"""
    dump_id = callback.data.split("_")[1]

    # Отправляем тектовое сообщение с описанием
    _, title, description = catalogs_db.select_row_by_id(int(dump_id))
    msg = msg_handle_item_selection(title, description)
    await callback.message.answer(text=msg, parse_mode="HTML")

    # Отправляем группу файлов
    photos_list = files_db.select_rows_by_id(dump_id)
    start_i = 0
    step = 10
    for i in range(0, len(photos_list), 10):
        items = photos_list[start_i: start_i + step]
        media_group = []

        for item in items:
            if item['file_name'].startswith('photo'):
                media_group.append(types.InputMediaPhoto(media=item['telegram_file_id']))
            elif item['file_name'].startswith('video'):
                media_group.append(types.InputMediaVideo(media=item['telegram_file_id']))
            else:
                continue
        start_i += step
        await callback.message.answer_media_group(media=media_group)
    # Подтверждаем обработку колбэка (убираем "часики")
    await callback.answer()


@router.callback_query(PaginationState.viewing_list, F.data.startswith("editdumpid_"))
async def handle_edit_dump(callback: types.CallbackQuery):
    """Обработка выбранного елемпнта дампа в режіме редактирования"""
    dump_id = callback.data.split("_")[1]
    _, title, _ = catalogs_db.select_row_by_id(int(dump_id))
    await callback.message.answer(text=title, parse_mode="HTML", reply_markup=await kb.edit_keyboard(dump_id))
    await callback.answer()


@router.callback_query(F.data.startswith("edit_description"))
async def handle_edit_description(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора элемента"""
    dump_id = callback.data.split(";")[1]
    await state.set_state(EditState.waiting_for_description)
    await state.update_data(dump_id=dump_id)
    await callback.answer()
    await callback.message.answer(text=msgs_process_title['input_description'], parse_mode="HTML")


@router.callback_query(F.data.startswith("edit_photos_dumpid"))
async def handle_edit_photos(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора элемента"""
    dump_id = callback.data.split(";")[1]
    await state.set_state(EditState.waiting_for_photos)
    await state.update_data(dump_id=dump_id, photos=[], file_names=[])
    await callback.answer()
    await callback.message.answer(text=msg_process_description, parse_mode="HTML", reply_markup=await kb.save_cancel_kb())
