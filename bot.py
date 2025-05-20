from config import config
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import cmd_start, cmd_new, cmd_show, cmd_edit, cmd_stop
from middlewares.ban import BanMiddleware  # Импортируем наш middleware
from callbacks import callback_handles
from text.messages import msgs_cmd
from backup_files import scheduled_backup


async def on_startup(bot: Bot):
    """Запуск бэкапа при старте бота"""
    asyncio.create_task(scheduled_backup())


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.startup.register(on_startup)  # Запуск бэкапа при старте

    dp.include_router(cmd_start.router)
    dp.include_router(cmd_new.router)
    dp.include_router(cmd_show.router)
    dp.include_router(cmd_edit.router)
    dp.include_router(callback_handles.router)
    dp.include_router(cmd_stop.router)

    dp.update.middleware(BanMiddleware())  # This connected middleware contains the logic for ignoring banned users

    # Set commands
    await bot.set_my_commands([
        BotCommand(command="show", description=msgs_cmd['show']),
        BotCommand(command="new", description=msgs_cmd['new']),
        BotCommand(command="edit", description=msgs_cmd['edit']),
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
