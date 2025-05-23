from aiogram import types, F, Router
from handlers.cmd_show import PaginationState
from keyboards.catalog_kb import build_dumps_keyboard_with_pagination
import keyboards.keyboards as kb
from services.database import catalogs_db, files_db
from text.messages import msg_handle_item_selection, msg_process_description, msgs_process_title, msg_del_dump_confirm
from handlers.cmd_edit import EditDump
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import asyncio
from concurrent.futures import ThreadPoolExecutor
from backup_files_controller import sync_get_archives_extract_files

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

    dump_id = callback.data.split(":")[1]  # catalog id
    _, title, description, _ = await catalogs_db.select_row_by_id(int(dump_id))  # get title and description grom db
    msg = msg_handle_item_selection(title, description)  # generate message
    # Sending a text message with description of catalog
    await callback.message.answer(text=msg, parse_mode="HTML")

    # Sending media group
    mediafiles_list = await files_db.select_rows_by_id(dump_id)

    """
    "If Telegram deleted the files after some time and the file ID doesn't work—download the corresponding archive, 
    extract the files, and send them to the user. This is the flag to enable this option."
    """
    flag = False  # init flag
    document_files_list = []
    """
    The Telegram bot cannot send more than 10 files at once 
    in a media group—this is a limitation of the service itself. 
    Therefore, we send the files from the list in batches, splitting them across multiple messages.
    """
    start_i = 0
    step = 10
    for i in range(0, len(mediafiles_list), 10):
        items = mediafiles_list[start_i: start_i + step]
        media_group = []

        for item in items:
            if item['file_name'].startswith('photo'):
                media_group.append(types.InputMediaPhoto(media=item['telegram_file_id']))
            elif item['file_name'].startswith('video'):
                media_group.append(types.InputMediaVideo(media=item['telegram_file_id']))
            elif item['file_name'].startswith('document'):
                document_files_list.append(item['telegram_file_id'])
            else:
                continue
        start_i += step
        try:
            await callback.message.answer_media_group(media=media_group)
            if document_files_list:
                await handle_send_document_type_files(callback, document_files_list)
        except Exception:
            flag = True
            break

    # Download archives from Google Drive, extract files to RAM(io.Bytes)
    if flag:

        executor = ThreadPoolExecutor(max_workers=5)
        loop = asyncio.get_running_loop()
        mediafiles_list = await loop.run_in_executor(executor, sync_get_archives_extract_files, dump_id)
        start_i = 0
        step = 10

        for i in range(0, len(mediafiles_list), 10):
            items = mediafiles_list[start_i: start_i + step]
            media_group = []
            for item in items:
                item['bytes'].seek(0)  # обязательно!
                file = types.BufferedInputFile(file=item['bytes'].read(), filename=item['file_name'])
                if item['file_name'].startswith('photo'):
                        media_group.append(types.InputMediaPhoto(media=file))
                elif item['file_name'].startswith('video'):
                    media_group.append(types.InputMediaVideo(media=file))
                elif item['file_name'].startswith('document'):
                    document_files_list.append(file)
                else:
                    continue
            start_i += step
            # Send files
            msg = await callback.message.answer_media_group(media=media_group)
            for indx, item in enumerate(msg):
                await files_db.update_fileid_by_file_name(items[indx]['file_name'], item.photo[-1].file_id)
            if document_files_list:
                await handle_send_document_type_files(callback, document_files_list)

    # Confirm callback processing
    try:
        await callback.answer()
        return
    except TelegramBadRequest:
        return


async def handle_send_document_type_files(callback: types.CallbackQuery, document_files_list: list):
    start_i = 0
    step = 10
    for i in range(0, len(document_files_list), 10):
        items = document_files_list[start_i: start_i + step]
        media_group = []

        for item in items:
            media_group.append(types.InputMediaDocument(media=item))
        start_i += step
        await callback.message.answer_media_group(media=media_group)




@router.callback_query(PaginationState.viewing_list, F.data.startswith("edit"))
async def handle_edit_dump(callback: types.CallbackQuery):
    """When a catalog is selected from list, sends user inline keyboard with edit options"""

    dump_id = callback.data.split(":")[1]
    _, title, _, _ = await catalogs_db.select_row_by_id(int(dump_id))
    # Build two buttons: add new description and add new files
    await callback.message.answer(text=title, parse_mode="HTML",
                                  reply_markup=await kb.edit_keyboard(dump_id)
                                  )
    await callback.answer()


@router.callback_query(F.data.startswith("descr_edit"))
async def handle_add_description(callback: types.CallbackQuery, state: FSMContext):
    """Edit description"""

    dump_id = callback.data.split(":")[1]
    await state.set_state(EditDump.waiting_for_description)
    await state.update_data(dump_id=dump_id)
    await callback.answer()
    await callback.message.answer(text=msgs_process_title['input_description'],
                                  parse_mode="HTML"
                                  )


@router.callback_query(F.data.startswith("file_edit"))
async def handle_add_photos(callback: types.CallbackQuery, state: FSMContext):
    """Edit files"""

    dump_id = callback.data.split(":")[1]
    await state.set_state(EditDump.waiting_for_mediafiles)
    await state.update_data(dump_id=dump_id, media_id_lst=[], file_names_lst=[])
    await callback.answer()
    await callback.message.answer(text=msg_process_description,
                                  parse_mode="HTML",
                                  reply_markup=await kb.save_cancel_kb()
                                  )


@router.callback_query(F.data.startswith("del_dump"))
async def handle_delete_category(callback: types.CallbackQuery, state: FSMContext):
    """Delete category from database"""

    dump_id = callback.data.split(":")[1]
    await state.set_state(EditDump.delete_catalog)
    await state.update_data(dump_id=dump_id)
    await callback.answer()
    await callback.message.answer(text=msg_del_dump_confirm,
                                  parse_mode="HTML",
                                  reply_markup=await kb.save_cancel_kb()
                                  )
