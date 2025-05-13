from config_file import config
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import cmd_start, cmd_new, cmd_show, cmd_edit, cmd_stop
from middlewares.ban import BanMiddleware  # Импортируем наш middleware
from callbacks import callback_handles


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(cmd_start.router)
    dp.include_router(cmd_new.router)
    dp.include_router(cmd_show.router)
    dp.include_router(cmd_edit.router)
    dp.include_router(callback_handles.router)
    dp.include_router(cmd_stop.router)

    dp.update.middleware(BanMiddleware())  # This connected middleware contains the logic for ignoring banned users

    # Set commands
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="show", description="Посмотреть все группы фотографий"),
        BotCommand(command="new", description="Создать новую группу фотографий"),
        BotCommand(command="edit", description="Редактировать группу фотографий"),
        BotCommand(command="stop", description="Редактировать группу фотографий")
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
