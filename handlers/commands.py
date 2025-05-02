from aiogram import Router, F
from aiogram.types import Message
from services.database import users_db
from config_file import config
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from text.messages import messages_cmd_start


router = Router()
users_db.init()  # Инициализируем экземпляр класса
PASSPHRASE = config.PASSPHRASE
MAX_ATTEMPTS_PASSPHRASE = 5  # Максимальное количество попыток ввода пароля, после которого выписывается бан


@router.message(Command("cancel"))
# --- Команда /cancel (сброс FSM вручную) ---
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    if current_state == AuthStates.waiting_for_password:
        return
    await message.answer("❌ Форма отменена. FSM сброшен.")
    await state.clear()  # Полный сброс состояния


# --- START ---
class AuthStates(StatesGroup):
    waiting_for_password = State()  # Состояние ожидания пароля


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # --- Команда /start, авторизация пользователя по пасс-фразе. В случае непрохождения - внесение в бан-лист ---
    user_id = message.chat.id
    # users_db.cache - словарь для работы с пользователями. key - int(tg_user_id), value - 1 or 2 or 3 (флаг)
    # for example {1234: 1, 4567:3}
    if users_db.cache.get(user_id, None):
        await message.answer(messages_cmd_start['user_is_auth'])
        return

    # Затыкает дыру, если прожимать комманду /start при активном FSM
    current_state = await state.get_state()
    if current_state == AuthStates.waiting_for_password:  # Если для данного пользователя есть состояние FSM
        await message.answer(messages_cmd_start['user_is_not_auth'])
    else:
        await state.set_state(AuthStates.waiting_for_password)  # Инициализируем FSM
        await state.update_data(attempts=0)  # Инициализируем счетчик попыток
        await message.answer(messages_cmd_start['demand_pass'])


@router.message(AuthStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    # --- Обработка введённой пасс-фразы от пользователя ---

    user_data = await state.get_data()
    attempts = user_data.get("attempts", 0) + 1  # Счётчик попыток ввода пасс-фразы

    if message.text == PASSPHRASE:
        #  Добавляем в список юзеров c флагом 1 (разрешение на запись и редактирование)
        users_db.cache[message.from_user.id] = 1
        users_db.insert(user_id=message.from_user.id, user_permission=1)  # Пишем в БД
        await message.answer("Пароль верный! Вы авторизованы.")
        await state.clear()
        return

    if attempts >= MAX_ATTEMPTS_PASSPHRASE:
        await message.answer("Превышено количество попыток. Вы заблокированы.")
        users_db.cache[message.from_user.id] = 3  # Добавляем в список юзеров c флагом 3 (забанен)
        users_db.insert(user_id=message.from_user.id, user_permission=3)  # Пишем в БД
        await state.clear()
        return

    await state.update_data(attempts=attempts)
    remaining = MAX_ATTEMPTS_PASSPHRASE - attempts
    await message.answer(f"Неверный пароль. Осталось попыток: {remaining}")


# --- START END ---

# --- CREATE ---
class CreateDump(StatesGroup):
    waiting_for_title = State()  # Ожидаем title
    waiting_for_description = State()  # Ожидаем description


@router.message(Command("create"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Укажите название события (не более 62 символов)\n/cancel - отменить создание нового дампа")
    await state.set_state(CreateDump.waiting_for_title)


@router.message(CreateDump.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    # --- Обработка title ---
    await state.update_data(title=message.text)  # Сохраняем title
    await message.answer("Добавьте описание")
    await state.set_state(CreateDump.waiting_for_description)


@router.message(CreateDump.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    # --- Обработка description ---
    data = await state.get_data()  # Получаем сохранённые данные
    title = data.get("title")
    description = message.text

    await message.answer(
        f"✅ Данные сохранены!\n {title} {description}"
    )
    await state.clear()  # Сбрасываем FSM

# --- CREATE END---

