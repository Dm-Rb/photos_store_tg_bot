from services.database import users_db
from aiogram import Bot
from text.messages import msg_notification


async def send_notification_all_users(notification_type, catalog_tittle, user_id_ignore):

    message = msg_notification(catalog_tittle, notification_type)
    for user_id in users_db.cache.keys():
        if user_id == user_id_ignore:
            continue
        if users_db.cache[user_id] == 3:  # Banned user
            continue
        await Bot.send_message(chat_id=user_id, text=message)

