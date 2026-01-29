from aiogram import Bot
from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.methods import SendMessage, SendPhoto, SendVideo, SendDocument
from aiogram.types import ReplyKeyboardMarkup

class NoButtonsInAdminChatMiddleware(BaseRequestMiddleware):
    def __init__(self, ignored_chat_id: int):
        self.ignored_chat_id = ignored_chat_id

    async def __call__(self, make_request, bot: Bot, method):

        chat_id = getattr(method, "chat_id", None)
        if chat_id == self.ignored_chat_id:
            
            markup = getattr(method, "reply_markup", None)
            
            if isinstance(markup, ReplyKeyboardMarkup):
                method.reply_markup = None
        
        return await make_request(bot, method)