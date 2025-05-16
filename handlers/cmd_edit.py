from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.catalog_kb import build_dumps_keyboard_with_pagination
from text.messages import msg_cmd_edit, msg_wrong_input_in_photos_state, msg_done, msg_notification
from services.database import catalogs_db, users_db, files_db
from pathlib import Path
from handlers.notifications import send_notification_all_users
import datetime


router = Router()
FILES_DIR = 'files'  # Tmp-dir for photos, video and archives
Path(FILES_DIR).mkdir(exist_ok=True)


class PaginationState(StatesGroup):
    viewing_list = State()  # FSM for pagination


class EditDump(StatesGroup):
    waiting_for_description = State()  # FSM for description
    waiting_for_mediafiles = State()  # FSM  for files
    delete_catalog = State()


@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext):
    """Initializes the logic for editing existing catalogs.
    Specifically, adding a new description and adding new files."""

    if not users_db.cache.get(message.from_user.id, None):
        return

    await state.set_state(PaginationState.viewing_list)
    await state.update_data(current_page=0)  # Start inline keyboard with first page
    # Shows an inline keyboard listing catalog names with pagination
    await message.answer(
        text=msg_cmd_edit,
        parse_mode="HTML",
        reply_markup=await build_dumps_keyboard_with_pagination(0, True)
    )  # <True> flag indicates in that the keyboard processes keystrokes in edit mode


@router.message(EditDump.waiting_for_description)
async def add_description(message: Message, state: FSMContext):
    """This handler is called from the <handle_edit_description> callback,
    which is triggered when an inline button is pressed.
    The handler writes data from <state.data> and the user's input message to the database."""

    data = await state.get_data()
    dump_id = data.get("dump_id", None)
    message_text = message.text
    if not message_text:
        return
    text = f"© {message.text.strip()}"
    await catalogs_db.update_description_by_id(dump_id, text)
    await state.clear()
    await message.answer(
        text=msg_done,
        parse_mode="HTML",
    )
    # Search <tittle>  of catalog by <id> from <catalogs_db.cache_list>
    result = [item['tittle'] for item in catalogs_db.cache_list if item['id'] == dump_id]
    title = result[0] if result else None
    bot = message.bot
    msg_text = msg_notification(title=title, type_='edit')
    await send_notification_all_users(bot, msg_text, user_ignore=message.from_user.id)
    # Updating a datetime cell value in the database
    datetime_record = datetime.datetime.now().replace(microsecond=0)
    await catalogs_db.update_datetime_by_id(id_=dump_id, datetime=datetime_record)


@router.message(EditDump.waiting_for_mediafiles, Command("save"))
async def handle_cmd_save_4_editdump(message: Message, state: FSMContext):
    """ Retrieves gathered data from <state.data>
        Saves data to database. Resets the state"""

    # Get data from <state>
    data = await state.get_data()
    dump_id = data.get("dump_id", None)
    media_id_lst = data.get("media_id_lst", [])
    file_names_lst = data.get("file_names_lst", [])

    # Iterating through the array and writing items to the database
    for media_id, file_name in zip(media_id_lst, file_names_lst):
        await files_db.insert(file_name, media_id, dump_id)

    await message.answer(msg_done, reply_markup=ReplyKeyboardRemove())
    await state.clear()
    # Updating a datetime cell value in the database
    datetime_record = datetime.datetime.now().replace(microsecond=0)
    await catalogs_db.update_datetime_by_id(id_=dump_id, datetime=datetime_record)


@router.message(EditDump.waiting_for_mediafiles)
async def wrong_input_in_photos_state(message: Message):
    """Handler for sending response when user provides invalid media data type"""

    await message.answer(text=msg_wrong_input_in_photos_state)

@router.message(EditDump.delete_catalog, Command("save"))
async def delete_catalog(message: Message, state: FSMContext):
    """Handler for sending response when user provides invalid media data type"""
    data = await state.get_data()
    dump_id = data.get("dump_id", None)
    await catalogs_db.delete_row_by_id(dump_id)
    await files_db.delete_rows_by_catalog_id(dump_id)
    await message.answer(msg_done, reply_markup=ReplyKeyboardRemove())
    await state.clear()

