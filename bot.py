from config import config
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import cmd_start, cmd_new, cmd_show, cmd_edit, cmd_stop, cmd_help
from middlewares.ban import BanMiddleware  # Импортируем наш middleware
from callbacks import callback_handles
from text.messages import msgs_cmd
from backup_files_controller import scheduled_backup
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

#
from backup_files_controller import files
from services.google_drive import google_drive
async def on_startup(bot: Bot):
    """Start scheduled backup"""
    # asyncio.create_task(scheduled_backup())
    asyncio.create_task(google_drive.upload_files(files))


async def main():
    # session = AiohttpSession(api=TelegramAPIServer.from_base("http://localhost:8081", is_local=True))
    # bot = Bot(token=config.BOT_TOKEN, session=session)
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.startup.register(on_startup)  # Registration scheduled backup to dispatcher

    dp.include_router(cmd_start.router)
    dp.include_router(cmd_new.router)
    dp.include_router(cmd_show.router)
    dp.include_router(cmd_edit.router)
    dp.include_router(cmd_help.router)
    dp.include_router(callback_handles.router)
    dp.include_router(cmd_stop.router)

    dp.update.middleware(BanMiddleware())  # This connected middleware contains the logic for ignoring banned users

    # Set commands
    await bot.set_my_commands([
        BotCommand(command="show", description=msgs_cmd['show']),
        BotCommand(command="new", description=msgs_cmd['new']),
        BotCommand(command="edit", description=msgs_cmd['edit']),
        BotCommand(command="help", description=msgs_cmd['help']),
        BotCommand(command="start", description=msgs_cmd['start']),
        BotCommand(command="stop", description=msgs_cmd['stop'])
    ])

    # Start long polling
    try:
        await dp.start_polling(bot)
    finally:
        # Close API client after end of work
        await bot.session.close()


if __name__ == "__main__":
    print('Start')
    asyncio.run(main())