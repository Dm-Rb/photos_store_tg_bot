from aiogram import Router
from aiogram.types import Message
from services.database import users_db
from config import config
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from text.messages import msgs_cmd_start, msgs_process_password


router = Router()
PASSPHRASE = config.PASSPHRASE
MAX_ATTEMPTS_PASSPHRASE = 5  # Maximum number of password attempts before a ban is issued


"""
Users flags:
1 - read and write
2 - only read
3 - banned
"""


class AuthStates(StatesGroup):
    waiting_for_password = State()  # Waiting for password


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Initializing user authentication with a passphrase. Failed attempts lead to banlist addition"""

    user_id = message.chat.id
    # -users_db.cache - dict with users work. key - int(tg_user_id), value - 1 or 2 or 3 (флаг)
    # -for example {1234: 1, 4567:3}
    if users_db.cache.get(user_id, None):
        await message.answer(msgs_cmd_start['user_is_auth'])
        return

    # Patches the hole when spamming /start command during active FSM
    current_state = await state.get_state()
    if current_state == AuthStates.waiting_for_password:   # If the user has an active state in FSM
        await message.answer(msgs_cmd_start['user_is_not_auth'])
    else:
        await state.set_state(AuthStates.waiting_for_password)  # Init FSM
        await state.update_data(attempts=0)  # Init try counter
        await message.answer(msgs_cmd_start['demand_pass'])


@router.message(AuthStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    """Processing of the user-entered passphrase"""

    user_data = await state.get_data()
    attempts = user_data.get("attempts", 0) + 1  # try counter

    if message.text == PASSPHRASE:
        #  Add to user list (user cache) with flag 1 (write and edit permission)
        users_db.cache[message.from_user.id] = 1
        await users_db.insert(user_id=message.from_user.id, user_permission=1)  # record to DB
        await message.answer(msgs_process_password['successful_auth'])
        await state.clear()
        return

    if attempts >= MAX_ATTEMPTS_PASSPHRASE:
        await message.answer(msgs_process_password['ban'])
        users_db.cache[message.from_user.id] = 3  # Add to user list (user cache) with flag 3 (ban)
        await users_db.insert(user_id=message.from_user.id, user_permission=3)  # Пишем в БД
        await state.clear()
        return

    await state.update_data(attempts=attempts)
    remaining = MAX_ATTEMPTS_PASSPHRASE - attempts
    try:
        await message.answer(msgs_process_password['invalid_pass'] + str(remaining))
    except TypeError:
        return
