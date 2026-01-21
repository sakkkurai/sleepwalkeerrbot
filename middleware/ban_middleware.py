from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from database.core import async_session_maker
from database.models import User

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self, 
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]], 
        event: Message | CallbackQuery, 
        data: Dict[str, Any]
    ) -> Any:
        
        user_id = event.from_user.id

        async with async_session_maker() as session:
            user = await session.get(User, user_id)

            if user and user.is_banned:
                if isinstance(event, CallbackQuery):
                    await event.answer("⛔️ Вы заблокированы.", show_alert=True)
                
                elif isinstance(event, Message):
                    await event.answer("<b>⛔️ Вы были заблокированы в боте.</b>\nХотите обжаловать блокировку? Свяжитесь с администратором канала — ссылка в закрепе.")
                
                return
            
        return await handler(event, data)