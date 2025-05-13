from aiogram import Router
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.catalog_kb import build_dumps_keyboard_with_pagination
from text.messages import msg_cmd_edit, msg_wrong_input_in_photos_state, msg_done
from services.database import catalogs_db, users_db, files_db
from pathlib import Path


router = Router()
FILES_DIR = 'files'  # Tmp-dir for photos, video and archives
Path(FILES_DIR).mkdir(exist_ok=True)


class PaginationState(StatesGroup):
    viewing_list = State()  # FSM for pagination


class EditDump(StatesGroup):
    waiting_for_description = State()  # FSM for description
    waiting_for_mediafiles = State()  # FSM  for files


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
    text = f"© {message.text.strip()}"
    catalogs_db.update_description_by_id(dump_id, text)
    await state.clear()
    await message.answer(
        text=msg_done,
        parse_mode="HTML",
    )


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
        files_db.insert(file_name, media_id, dump_id)

    await message.answer(msg_done, reply_markup=ReplyKeyboardRemove())
    await state.clear()


@router.message(EditDump.waiting_for_mediafiles)
async def wrong_input_in_photos_state(message: Message):
    """Handler for sending response when user provides invalid media data type"""

    await message.answer(text=msg_wrong_input_in_photos_state)
