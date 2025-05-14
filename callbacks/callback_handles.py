from aiogram import types, F, Router
from handlers.cmd_show import PaginationState
from keyboards.catalog_kb import build_dumps_keyboard_with_pagination
import keyboards.keyboards as kb
from services.database import catalogs_db, files_db
from text.messages import msg_handle_item_selection, msg_process_description, msgs_process_title
from handlers.cmd_edit import EditDump
from aiogram.fsm.context import FSMContext


router = Router()


@router.callback_query(PaginationState.viewing_list, F.data.in_(["prev_page", "next_page"]))
async def handle_page_change(callback: types.CallbackQuery, state: FSMContext):
    """Keyboard button pagination handler"""

    data = await state.get_data()
    current_page = data.get("current_page", 0)
    if callback.data == "prev_page":
        new_page = current_page - 1
    else:
        new_page = current_page + 1

    # Refresh <state>
    await state.update_data(current_page=new_page)

    # Edit message and keyboards
    await callback.message.edit_text(
        callback.message.text,  # Keep the same text
        reply_markup=await build_dumps_keyboard_with_pagination(new_page)  # Change keyboard contents
    )
    # Confirm callback processing
    await callback.answer()


@router.callback_query(PaginationState.viewing_list, F.data.startswith("show"))
async def handle_show_dump(callback: types.CallbackQuery):
    """Processes inline keyboard callbacks for catalog navigation"""

    dump_id = callback.data.split(":")[1]
    _, title, description, _ = catalogs_db.select_row_by_id(int(dump_id))
    msg = msg_handle_item_selection(title, description)
    # Sending a text message with description of catalog
    await callback.message.answer(text=msg, parse_mode="HTML")

    # Sending media group
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
    # Confirm callback processing
    await callback.answer()


@router.callback_query(PaginationState.viewing_list, F.data.startswith("edit"))
async def handle_edit_dump(callback: types.CallbackQuery):
    """When a catalog is selected from list, sends user inline keyboard with edit options"""

    dump_id = callback.data.split(":")[1]
    _, title, _, _ = catalogs_db.select_row_by_id(int(dump_id))
    # Build two buttons: add new description and add new files
    await callback.message.answer(text=title, parse_mode="HTML", reply_markup=await kb.edit_keyboard(dump_id))
    await callback.answer()


@router.callback_query(F.data.startswith("descr_edit"))
async def handle_edit_description(callback: types.CallbackQuery, state: FSMContext):
    """Edit description"""

    dump_id = callback.data.split(":")[1]
    await state.set_state(EditDump.waiting_for_description)
    await state.update_data(dump_id=dump_id)
    await callback.answer()
    await callback.message.answer(text=msgs_process_title['input_description'], parse_mode="HTML")


@router.callback_query(F.data.startswith("file_edit"))
async def handle_edit_photos(callback: types.CallbackQuery, state: FSMContext):
    """Edit files"""

    dump_id = callback.data.split(":")[1]
    await state.set_state(EditDump.waiting_for_mediafiles)
    await state.update_data(dump_id=dump_id, media_id_lst=[], file_names_lst=[])
    await callback.answer()
    await callback.message.answer(text=msg_process_description, parse_mode="HTML", reply_markup=await kb.save_cancel_kb())
