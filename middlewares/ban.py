from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Dict, Any, Callable, Awaitable
from services.database import users_db


class BanMiddleware(BaseMiddleware):
    """
    Middleware for blocking users from a ban list.
    If a user has flag 3 — their messages are ignored.
    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:

        # Get
        user = data.get("event_from_user")
        # 3 - а flag indicating the user's status (3 means banned)
        if users_db.cache.get(user.id, None) and users_db.cache[user.id] == 3:
            return
        # If the user isn't banned, forward the message to the handler
        return await handler(event, data)
