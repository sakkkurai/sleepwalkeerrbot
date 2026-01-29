import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database.core import init_db
from middleware.album import AlbumMiddleware
from middleware.ban_middleware import BanMiddleware
from middleware.register_check import RegisterCheckMiddleware
from middleware.no_admin_buttons import NoButtonsInAdminChatMiddleware
from handlers import submission, user_profile, admin, help, other

logging.basicConfig(level=logging.INFO)

async def on_startup():
    print("🔄 Connecting to database...")
    await init_db()
    print("✅ Database and tables created successfully!")

async def main():
    bot = Bot(
        token=config.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    bot.session.middleware(NoButtonsInAdminChatMiddleware(config.MODERATION_CHAT_ID))
    
    dp = Dispatcher()
    dp.message.outer_middleware(BanMiddleware())
    dp.callback_query.outer_middleware(BanMiddleware())
    dp.message.outer_middleware(RegisterCheckMiddleware())
    dp.callback_query.outer_middleware(RegisterCheckMiddleware())
    dp.message.middleware(AlbumMiddleware())
    dp.include_router(user_profile.router)
    dp.include_router(submission.router)
    dp.include_router(admin.router)
    dp.include_router(help.router)
    dp.include_router(other.router)

    dp.startup.register(on_startup)

    
    print("🚀 Bot started, click Ctrl+C to stop.")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot was stopped by user.")