from services.database import users_db
from aiogram import Bot


async def send_notification_all_users(bot: Bot, msg_text, user_ignore):
    # Пример списка user_id

    for user_id in users_db.cache.keys():
        if user_id == user_ignore:
            continue
        if users_db.cache[user_id] == 3:
            continue

        # try:
        await bot.send_message(chat_id=user_id, text=msg_text, parse_mode='HTML')
        # except TelegramAPIError as e:
        #     # Можно логировать ошибку
        #     print(f"Не удалось отправить сообщение {user_id}: {e}")
