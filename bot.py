import asyncio
import os
import psutil
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from database.core import init_db
from middleware.album import AlbumMiddleware
from middleware.user_control import UserControlMiddleware
from middleware.no_admin_buttons import NoButtonsInAdminChatMiddleware
from handlers import errors, submission, user_profile, admin, help, other

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
    process = psutil.Process(os.getpid())
    bot.session.middleware(NoButtonsInAdminChatMiddleware(config.MODERATION_CHAT_ID))

    dp = Dispatcher()
    dp.include_router(errors.router)
    dp.message.outer_middleware(UserControlMiddleware())
    dp.callback_query.outer_middleware(UserControlMiddleware())
    dp.message.middleware(AlbumMiddleware())
    dp.include_router(user_profile.router)
    dp.include_router(submission.router)
    dp.include_router(admin.router)
    dp.include_router(help.router)
    dp.include_router(other.router)

    dp.startup.register(on_startup)


    print("🚀 Bot started, click Ctrl+C to stop.")


    await bot.delete_webhook(drop_pending_updates=True)
    print(f"RAM: {process.memory_info().rss / 1024**2:.2f} MB")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Bot was stopped by user.")
