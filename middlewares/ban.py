from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Dict, Any, Callable, Awaitable
from services.database import users_db


users_db.init()


class BanMiddleware(BaseMiddleware):
    """
    Middleware для блокировки пользователей из бан-листа.
    Если пользователь имеет флаг 4 — его сообщения игнорируются.
    """

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        """
        :param handler: Оригинальный обработчик (хэндлер), который должен быть вызван.
        :param event: Событие (сообщение, callback и т.д.).
        :param data: Дополнительные данные (например, пользователь, бот, FSM и т.д.).
        :return: Результат работы handler или None (если пользователь забанен).
        """

        # Получаем пользователя из данных (если он есть)
        user = data.get("event_from_user")
        # 3 - Флаг, означающий статус пользователя (3 - это бан)
        if users_db.cache.get(user.id, None) and users_db.cache[user.id] == 3:
            # Прерываем дальнейшую обработку
            return

        # Если пользователь не забанен — передаём сообщение дальше в хэндлер
        return await handler(event, data)
