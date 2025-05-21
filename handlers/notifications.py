from services.database import users_db
from aiogram import Bot


async def send_notification_all_users(bot: Bot, msg_text, user_ignore):
    """
    Send a catalog update notification to all users except banned ones and the user who initiated the catalog update.
    """

    for user_id in users_db.cache.keys():
        if user_id == user_ignore:
            continue
        if users_db.cache[user_id] == 3:
            continue
        await bot.send_message(chat_id=user_id, text=msg_text, parse_mode='HTML')
