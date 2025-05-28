from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from text.messages import msg_help


router = Router()


@router.message(Command('help'))
async def cmd_stop(messages: Message):
    """Show information about bot"""
    await messages.answer(text=msg_help, parse_mode='HTML')