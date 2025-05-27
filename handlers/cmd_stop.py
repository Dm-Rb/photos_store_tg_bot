from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.database import users_db
from text.messages import msg_cmd_stop


router = Router()


@router.message(Command('stop'))
async def cmd_stop(messages: Message):
    """Delete user_id from data base"""

    user_id = messages.from_user.id
    if not users_db.cache.get(user_id, None):
        return

    await users_db.delete(user_id)
    del users_db.cache[user_id]
    await messages.answer(text=msg_cmd_stop)
