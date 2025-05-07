from aiogram import Router, F
from aiogram.types import Message
from services.database import users_db
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os
from pathlib import Path
from services.database import dumps_db, files_db

router = Router()
users_db.init()  # Инициализируем экземпляр класса
PHOTOS_DIR = 'temp'
Path(PHOTOS_DIR).mkdir(exist_ok=True)


@router.message(Command("cancel"))
# --- Команда /cancel (сброс FSM вручную) ---
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await message.answer("❌ Форма отменена. FSM сброшен.", reply_markup=ReplyKeyboardRemove())
    await state.clear()  # Полный сброс состояния


# --- CREATE ---
class PhotoDump(StatesGroup):
    waiting_for_title = State()  # Ожидаем title
    waiting_for_description = State()  # Ожидаем description
    waiting_for_photos = State()  # Ожидаем файлы


@router.message(Command("create"))
async def cmd_photos(message: Message, state: FSMContext):
    await message.answer(
        "Укажите название для набора фотографий (не более 62 символов)\n"
        "/cancel - отменить создание"
    )
    await state.set_state(PhotoDump.waiting_for_title)


@router.message(PhotoDump.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    if len(message.text) > 62:
        await message.answer("Название слишком длинное. Максимум 62 символа. Попробуйте еще раз")
        return

    await state.update_data(title=message.text)
    await message.answer("Теперь добавьте описание")
    await state.set_state(PhotoDump.waiting_for_description)


@router.message(PhotoDump.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    # await message.answer(
    #     "Теперь загрузите фотографии (одну или несколько).\n"
    #     "Когда закончите, введите команду /save для сохранения"
    # )
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/save"),
                KeyboardButton(text="/cancel ❌"),
            ]
        ],
        resize_keyboard=True
    )
    await message.answer(text='Загрузите фотографии (одну или несколько)\nКогда закончите, введите команду /save для сохранения', reply_markup=kb)
    await state.set_state(PhotoDump.waiting_for_photos)
    # Инициализируем список для хранения информации о фото
    await state.update_data(photos=[], file_names=[])


@router.message(PhotoDump.waiting_for_photos, Command("save"))
async def save_dump(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title", "Без названия")
    description = data.get("description", "Без описания")
    photos = data.get("photos", [])
    file_names = data.get("file_names", [])
    if not photos:
        await message.answer(
            "❌ Вы не отправили ни одной фотографии перед сохранением!\n"
            "Пожалуйста, отправьте фото, а затем используйте /save",
        )
        return
    result_message = {"title": title,
                      'description': description,
                      'photos': [{'telegram_file_id': file_id, 'file_name': file_name} for file_id,file_name in zip(photos, file_names)]
                      }
    dump_id = dumps_db.insert(result_message['title'], result_message['description'])
    for photo_item in result_message['photos']:
        files_db.insert(photo_item['file_name'], photo_item['telegram_file_id'], dump_id)
    await message.answer("Готово", reply_markup=ReplyKeyboardRemove())
    await state.clear()


@router.message(PhotoDump.waiting_for_photos, F.photo)
async def handle_photos(message: Message, state: FSMContext):
    # Получаем фото с самым высоким разрешением
    photo = message.photo[-1]

    # Создаем уникальное имя файла
    file_name = f"photo_{message.from_user.id}_{photo.file_unique_id}.jpg"
    file_path = os.path.join(PHOTOS_DIR, file_name)

    # Скачиваем фото
    file = await message.bot.get_file(photo.file_id)
    await message.bot.download_file(file.file_path, file_path)

    # Обновляем данные в состоянии
    data = await state.get_data()
    photos = data.get("photos", [])
    file_names = data.get("file_names", [])


    photos.append(photo.file_id)
    file_names.append(file_name)

    await state.update_data(photos=photos, file_names=file_names)

@router.message(PhotoDump.waiting_for_photos)
async def wrong_input_in_photos_state(message: Message):
    await message.answer("Пожалуйста, загружайте только фотографии. Когда закончите, введите /save")

# --- CREATE END---
