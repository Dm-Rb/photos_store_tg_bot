from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.catalog_kb import build_dumps_keyboard_with_pagination
from text.handlers_txt import msg_cmd_edit
from services.database import catalogs_db, users_db


router = Router()


class PaginationState(StatesGroup):
    viewing_list = State()  # Состояние просмотра списка


class EditState(StatesGroup):
    waiting_for_description = State()  # Ожидаем description
    waiting_for_photos = State()  # Ожидаем файлы


@router.message(Command("edit"))
async def cmd_edit(message: Message, state: FSMContext):
    """Обработка команды /show - инициализация пагинации"""

    if not users_db.cache.get(message.from_user.id, None):
        return

    await state.set_state(PaginationState.viewing_list)
    await state.update_data(current_page=0)  # Начинаем с первой страницы
    await message.answer(
        text=msg_cmd_edit,
        parse_mode="HTML",
        reply_markup=await build_dumps_keyboard_with_pagination(0, True)
    )


@router.message(EditState.waiting_for_description)
async def add_description(message: Message, state: FSMContext):
    """Обработка команды /show - инициализация пагинации"""
    data = await state.get_data()
    dump_id = data.get("dump_id", None)
    text = message.text.strip()
    catalogs_db.update_description_by_id(dump_id, text)
    await state.clear()
    await message.answer(
        text='description was update',
        parse_mode="HTML",
    )


# @router.message(EditState.waiting_for_photos, Command("save"))
# async def save_photos(message: Message, state: FSMContext):
#     data = await state.get_data()
#     photos = data.get("photos", [])
#     file_names = data.get("file_names", [])
#     if not photos:
#         await message.answer(text=msg_save_dump, parse_mode='HTML')
#         return
#     result_message = {"title": title,
#                       'description': "© " + description,
#                       'photos': [{'telegram_file_id': file_id, 'file_name': file_name} for file_id, file_name in zip(photos, file_names)]
#                       }
#     dump_id = catalogs_db.insert(result_message['title'], result_message['description'])
#     for photo_item in result_message['photos']:
#         files_db.insert(photo_item['file_name'], photo_item['telegram_file_id'], dump_id)
#     await message.answer("Готово", reply_markup=ReplyKeyboardRemove())
#     await state.clear()
#
#
# @router.message(MemoryDump.waiting_for_photos, F.photo)
# async def handle_photos(message: Message, state: FSMContext):
#     # Получаем фото с самым высоким разрешением
#     photo = message.photo[-1]
#
#     # Создаем уникальное имя файла
#     file_name = f"photo_{message.from_user.id}_{photo.file_unique_id}.jpg"
#     file_path = os.path.join(PHOTOS_DIR, file_name)
#
#     # Скачиваем фото
#     file = await message.bot.get_file(photo.file_id)
#     await message.bot.download_file(file.file_path, file_path)
#
#     # Обновляем данные в состоянии
#     data = await state.get_data()
#     photos = data.get("photos", [])
#     file_names = data.get("file_names", [])
#
#     photos.append(photo.file_id)
#     file_names.append(file_name)
#
#     await state.update_data(photos=photos, file_names=file_names)
#
#
# @router.message(MemoryDump.waiting_for_photos)
# async def wrong_input_in_photos_state(message: Message):
#     await message.answer(text=msg_wrong_input_in_photos_state)