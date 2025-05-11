from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove
from keyboards.keyboards import save_cancel_kb
import os
from pathlib import Path
from services.database import catalogs_db, files_db, users_db
from text.handlers_txt import msg_cmd_cancel, msg_cmd_photos, msgs_process_title, \
    msg_process_description, msg_wrong_input_in_photos_state, msg_save_dump


router = Router()
PHOTOS_DIR = 'files'  # Tmp-dir for photos, video and archives
Path(PHOTOS_DIR).mkdir(exist_ok=True)


class MemoryDump(StatesGroup):
    waiting_for_title = State()  # FSM for title
    waiting_for_description = State()  # FSM for description
    waiting_for_mediafiles = State()  # FSM  for files


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Resets the FSM states when triggered"""

    current_state = await state.get_state()  # Extract data from the state object
    if current_state is None:
        return
    await message.answer(text=msg_cmd_cancel, reply_markup=ReplyKeyboardRemove())
    await state.clear()


@router.message(Command("create"))
async def cmd_photos(message: Message, state: FSMContext):
    """Initializes a pipeline that creates and populates a new directory"""
    if not users_db.cache.get(message.from_user.id, None):
        return


    await message.answer(text=msg_cmd_photos, parse_mode='HTML')
    await state.set_state(MemoryDump.waiting_for_title)  # first step it is input title. Set FSM


@router.message(MemoryDump.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Handler that intercepts user-entered title"""
    if len(message.text) > 64:
        await message.answer(msgs_process_title['title_too_long'], parse_mode='HTML')
        return
    if message.text in [i['title'] for i in catalogs_db.cache_list]:
        await message.answer(text=msgs_process_title['title_is_exist'], parse_mode='HTML')
        return

    await state.update_data(title=message.text)
    # Prompt user to enter description and switch FSM state
    await message.answer(text=msgs_process_title['input_description'], parse_mode='HTML')
    await state.set_state(MemoryDump.waiting_for_description)


@router.message(MemoryDump.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Handler that intercepts user-entered description"""
    # # Intercept user message and store in <state.data>
    await state.update_data(description=message.text)
    # Buttons for user-friendly
    kb = await save_cancel_kb()
    # Prompt user to upload photos or videos and switch FSM state
    await message.answer(text=msg_process_description, parse_mode='HTML', reply_markup=kb)
    await state.set_state(MemoryDump.waiting_for_mediafiles)
    # Initialized empty lists in <state>
    await state.update_data(media_id_lst=[], file_names_lst=[])


@router.message(MemoryDump.waiting_for_mediafiles, F.photo | F.video)
async def handle_photos(message: Message, state: FSMContext):
    """This handler intercepts a media file or media group (videos/images) sent by user.
       The files are downloaded locally and their data is stored to <state.data>"""

    if message.photo:
        # Processing photo
        media = message.photo[-1]
        # ^ When user sends a single photo, Telegram API returns a list of photos in different qualities (thumbnails).
        # We take the highest quality version.
        file_ext = "jpg"
        file_name_start = 'photo'
    elif message.video:
        # Processing video
        media = message.video
        file_ext = message.video.mime_type.split("/")[-1]
        file_name_start = 'video'
    else:
        return
    # Create a unique file name
    file_name = f"{file_name_start}_{message.from_user.id}_{media.file_unique_id}.{file_ext}"
    file_path = os.path.join(PHOTOS_DIR, file_name)

    # Download file
    file = await message.bot.get_file(media.file_id)
    await message.bot.download_file(file.file_path, file_path)

    # Update data in FSM
    data = await state.get_data()
    media_id_lst = data.get("media_id_lst", [])
    file_names_lst = data.get("file_names_lst", [])

    media_id_lst.append(media.file_id)
    file_names_lst.append(file_name)

    await state.update_data(media_id_lst=media_id_lst, file_names_lst=file_names_lst)


@router.message(MemoryDump.waiting_for_mediafiles, Command("save"))
async def handle_cmd_save(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title", None)
    if not title:
        return
    description = data.get("description", None)
    media_id_lst = data.get("media_id_lst", [])
    file_names_lst = data.get("file_names_lst", [])
    if not media_id_lst:
        await message.answer(text=msg_save_dump, parse_mode='HTML')
        return

    media_groups = [{'file_id': file_id, 'file_name': file_name} for file_id, file_name in zip(media_id_lst, file_names_lst)]
    result_message = {"title": title,
                      'description': "© " + description,
                      'media_groups': media_groups
                      }
    dump_id = catalogs_db.insert(result_message['title'], result_message['description'])
    for photo_item in result_message['media_groups']:
        files_db.insert(photo_item['file_name'], photo_item['file_id'], dump_id)
    await message.answer("Готово", reply_markup=ReplyKeyboardRemove())
    await state.clear()




@router.message(MemoryDump.waiting_for_mediafiles)
async def wrong_input_in_photos_state(message: Message):
    await message.answer(text=msg_wrong_input_in_photos_state)
