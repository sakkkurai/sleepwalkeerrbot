from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from database.core import async_session_maker
from database.models import User

class UserControlMiddleware(BaseMiddleware):
    async def __call__(
        self, 
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], 
        event: Message | CallbackQuery, 
        data: Dict[str, Any]
    ) -> Any:
        
        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        tg_user = event.from_user

        async with async_session_maker() as session:
            user = await session.get(User, user_id)

            if user and user.is_banned:
                if isinstance(event, CallbackQuery):
                    await event.answer("⛔️ Вы заблокированы.", show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(
                        "<b>⛔️ Вы были заблокированы в боте.</b>\n"
                        "Хотите обжаловать блокировку? Свяжитесь с администратором канала — актуальный контакт находится в описании канала."
                    )
                return

            if not user:
                new_user = User(
                    user_id=user_id,
                    username=tg_user.username,
                    full_name=tg_user.full_name
                )
                session.add(new_user)
                await session.commit()
                print(f"🆕 Авто-регистрация: {tg_user.full_name} ({user_id})")
            else:
                if user.username != tg_user.username:
                    user.username = tg_user.username
                    await session.commit()
                    print(f"🔄 Юзернейм обновлен для {user_id}: {tg_user.username}")

        return await handler(event, data)