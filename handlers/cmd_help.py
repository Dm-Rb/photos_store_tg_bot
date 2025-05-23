from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from services.database import users_db
from text.messages import msg_help


router = Router()


@router.message(Command('help'))
async def cmd_stop(messages: Message):
    """Show information about"""
    await messages.answer(text=msg_help, parse_mode='HTML')