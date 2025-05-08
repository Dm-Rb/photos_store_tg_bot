from aiogram import Router
from aiogram.types import Message
from services.database import users_db
from config_file import config
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from text.handlers_txt import msgs_cmd_start, msgs_process_password


router = Router()
PASSPHRASE = config.PASSPHRASE
MAX_ATTEMPTS_PASSPHRASE = 5  # Максимальное количество попыток ввода пароля, после которого выписывается бан


# --- START ---
class AuthStates(StatesGroup):
    waiting_for_password = State()  # Состояние ожидания пароля


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    # --- Команда /start, авторизация пользователя по пасс-фразе. В случае непрохождения - внесение в бан-лист ---
    user_id = message.chat.id
    # -users_db.cache - словарь для работы с пользователями. key - int(tg_user_id), value - 1 or 2 or 3 (флаг)
    # -for example {1234: 1, 4567:3}
    if users_db.cache.get(user_id, None):
        await message.answer(msgs_cmd_start['user_is_auth'])
        return

    # Затыкает дыру, если прожимать комманду /start при активном FSM
    current_state = await state.get_state()
    if current_state == AuthStates.waiting_for_password:  # Если для данного пользователя есть состояние FSM
        await message.answer(msgs_cmd_start['user_is_not_auth'])
    else:
        await state.set_state(AuthStates.waiting_for_password)  # Инициализируем FSM
        await state.update_data(attempts=0)  # Инициализируем счетчик попыток
        await message.answer(msgs_cmd_start['demand_pass'])


@router.message(AuthStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    # --- Обработка введённой пасс-фразы от пользователя ---

    user_data = await state.get_data()
    attempts = user_data.get("attempts", 0) + 1  # Счётчик попыток ввода пасс-фразы

    if message.text == PASSPHRASE:
        #  Добавляем в список юзеров c флагом 1 (разрешение на запись и редактирование)
        users_db.cache[message.from_user.id] = 1
        users_db.insert(user_id=message.from_user.id, user_permission=1)  # Пишем в БД
        await message.answer(msgs_process_password['successful_auth'])
        await state.clear()
        return

    if attempts >= MAX_ATTEMPTS_PASSPHRASE:
        await message.answer(msgs_process_password['ban'])
        users_db.cache[message.from_user.id] = 3  # Добавляем в список юзеров c флагом 3 (забанен)
        users_db.insert(user_id=message.from_user.id, user_permission=3)  # Пишем в БД
        await state.clear()
        return

    await state.update_data(attempts=attempts)
    remaining = MAX_ATTEMPTS_PASSPHRASE - attempts
    await message.answer(msgs_process_password['invalid_pass'] + remaining)

# --- START END ---
