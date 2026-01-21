from aiogram import F, types, Router, Bot, html
from aiogram.fsm.context import FSMContext
from keyboards.reply import get_help_kb, get_main_reply_keyboard, get_back_kb
from states import UserState
from config import config

router = Router()

@router.message(F.text == "✝️ Нужна помощь!")
async def cmd_help(msg: types.Message):
    await msg.answer("<i>🧐 Чем могу помочь?</i>", reply_markup=get_help_kb())





@router.message(F.text == "👨‍💻 Связаться с поддержкой")
async def contact_with_moder(msg: types.Message, state: FSMContext):
    await msg.answer("<b>🐙 Напишите ваше сообщение.</b>\n<i>Оно будет отправлено модераторам.</i>", reply_markup=get_back_kb())
    await state.set_state(UserState.send_msg_to_moderation)


@router.message(UserState.send_msg_to_moderation)
async def proccess_user_msg_to_moderation(msg: types.Message, state: FSMContext, bot: Bot):

    if not msg.text:
        await msg.answer("<b>❌ Пожалуйста, отправьте текстовое сообщение.</b>")
        return
    
    user_text = html.quote(msg.text)
    user_name = html.quote(msg.from_user.full_name)
    user_link = f"tg://user?id={msg.from_user.id}"
    
    text_to_admin = (
        f"<b>♿ НОВОЕ СООБЩЕНИЕ ОТ <a href='{user_link}'>{user_name}</a>!</b>\n"
        f"<b>🆔 ID:</b> <code>{msg.from_user.id}</code>\n"
        f""
        f"<blockquote>{user_text}</blockquote>\n\n"
        f"<i>📋 Ответить:</i>\n"
        f"<code>/reply {msg.from_user.id} </code>"
    )
    
    try:
        await bot.send_message(chat_id=config.MODERATION_CHAT_ID, text=text_to_admin)
        await msg.answer("<b>🍄 Ваше сообщение отправлено модераторам.</b>", reply_markup=get_main_reply_keyboard())
    except Exception as e:
        await msg.answer("<b>❌ Ошибка отправки. Попробуйте позже.</b>")
        print(f"Ошибка поддержки: {e}")

    await state.clear()

@router.message(F.text == "❗ Правила для отправки постов")
async def rules_of_posts(message: types.Message):
    text = (
            "<b>❗ Правила для одобрения постов</b>\n\n"
            "<i>1. Фотки должны быть сделаны исключительно тобой, а не взяты с других ресурсов.\n"
            "2. Фото не должны иметь жёсткий провокационный/агрессивный характер — нельзя отправлять NSFW, свастики, фото с ярым политическим подтекстом и т.д.\n"
            "3. Постарайся не отправлять один и тот же пост.\n"
            "4. Если есть пара дублей, с которыми вы не можете определиться, отправляйте все — мы отберем!\n"
            "5. Отправляя медиа в этот канал, вы автоматически соглашаетесь, что они будут в публичном доступе.</i>"
        )

    await message.answer(text, reply_markup=get_main_reply_keyboard())