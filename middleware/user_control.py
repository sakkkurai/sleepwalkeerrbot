from datetime import datetime
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware, html
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
            if user and user.banned_reason is not None:
            
                if user.banned_until is None:
                    reason_text = f"\n📝 Причина: {html.quote(user.banned_reason)}"
                    
                    if isinstance(event, CallbackQuery):
                        await event.answer("⛔️ Вы заблокированы навсегда.", show_alert=True)
                    elif isinstance(event, Message):
                        await event.answer(f"<b>⛔️ Вы заблокированы в боте НАВСЕГДА.</b>{reason_text}")
                    return

                else:
                    if user.banned_until > datetime.utcnow():
                        reason_text = f"\n📝 Причина: {html.quote(user.banned_reason)}"
                        formatted_date = user.banned_until.strftime('%d.%m.%Y %H:%M')
                        
                        if isinstance(event, CallbackQuery):
                            await event.answer("⛔️ Вы временно заблокированы.", show_alert=True)
                        elif isinstance(event, Message):
                            await event.answer(f"<b>⛔️ Вы заблокированы в боте до {formatted_date} UTC.</b>{reason_text}")
                        return
                    else:
                        user.banned_until = None
                        user.banned_reason = None
                        await session.commit()
                        print(f"🔓 Срок бана истек. Пользователь {user_id} автоматически разбанен.")
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