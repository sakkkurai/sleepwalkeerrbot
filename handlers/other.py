from aiogram import Router, types
from aiogram.filters import StateFilter
from keyboards.reply import get_main_reply_keyboard
from config import config

router = Router()

@router.message(StateFilter(None)) 
async def echo_send_menu(message: types.Message):
    if message.chat.id == config.MODERATION_CHAT_ID:
        return
    
    await message.answer(
        "🤔 <b>Я тебя не понял.</b>\n\n"
        "<i>Пожалуйста, используй кнопки меню или пришли мне контент (фото/видео).</i>",
        reply_markup=get_main_reply_keyboard()
    )