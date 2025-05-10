from config_file import config
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from handlers import cmd_start, cmd_create, cmd_show, cmd_edit
from middlewares.ban import BanMiddleware  # Импортируем наш middleware
from callbacks import dumps_processing


async def main():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    # ---

    # подключаем роутеры к диспетчеру
    dp.include_router(cmd_start.router)
    dp.include_router(cmd_create.router)
    dp.include_router(cmd_show.router)
    dp.include_router(cmd_edit.router)
    dp.include_router(dumps_processing.router)


    dp.update.middleware(BanMiddleware())  # Будет применяться ко всем событиям

    # Устанавливаем команды бота
    await bot.set_my_commands([
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="create", description="Создать новую группу фотографий"),
        BotCommand(command="show", description="Посмотреть все группы фотографий")
    ])

    # Запускаем long polling
    try:
        await dp.start_polling(bot)
    finally:
        # Закрываем API клиент после завершения работы
        await bot.session.close()


if __name__ == "__main__":
    print('start')
    asyncio.run(main())
