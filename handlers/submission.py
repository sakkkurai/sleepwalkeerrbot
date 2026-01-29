from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, delete
from aiogram import html

from database.core import async_session_maker
from database.models import User, Post
from states import UserState
from utils.admin_utils import send_post_to_moderation
from keyboards.reply import get_skip_cancel_kb, get_confirm_kb, get_main_reply_keyboard
from aiogram.utils.chat_action import ChatActionSender

router = Router()

@router.message(F.photo | F.video | F.document)
async def handle_media_submission(message: types.Message, state: FSMContext, album: list[types.Message] = None):
    await state.clear()

    if not album:
        album = [message]

    if len(album) > 10:
        await message.answer("⚠️ Максимум 10 файлов. Лишние обрезаны.")
        album = album[:10]

    media_content = []
    caption = None
    
    for msg in album:
        if msg.caption and caption is None:
            caption = msg.caption
            
        if msg.photo:
            media_content.append({"type": "photo", "file_id": msg.photo[-1].file_id})
        elif msg.video:
            media_content.append({"type": "video", "file_id": msg.video.file_id})
        elif msg.document:
            media_content.append({"type": "document", "file_id": msg.document.file_id})

    async with async_session_maker() as session:
        new_post = Post(
            user_id=message.from_user.id,
            media_group_id=message.media_group_id,
            caption=caption,
            media_content=media_content,
            status="draft"
        )
        session.add(new_post)
        await session.flush()
        post_id = new_post.id
        await session.commit()

    await state.update_data(current_post_id=post_id)

    files_count = len(media_content)

    if caption:
        safe_caption = html.quote(caption)
        await message.answer(
            f"<b>📥 Принято {files_count} файлов.</b>\n\n"
            f"📝 <b>Описание:</b> {safe_caption}\n\n"
            f"<i>Отправляем?</i>",
            reply_markup=get_confirm_kb()
        )
        await state.set_state(UserState.confirm_sending)
        
    else:
        await message.answer(
            f"<b>📥 Принято {files_count} файлов без описания.</b>\n"
            f"<i>👇🏻 Напиши описание к посту, или нажми кнопку:</i>",
            reply_markup=get_skip_cancel_kb()
        )
        await state.set_state(UserState.submit_content)


@router.message(F.text == "❌ Отмена", UserState.submit_content)
@router.message(F.text == "❌ Отмена", UserState.confirm_sending)
async def cancel_submission(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("current_post_id")
    
    if post_id:
        async with async_session_maker() as session:
            post = await session.get(Post, post_id)
            if post:
                await session.delete(post)
                await session.commit()

    await message.answer("<i>❌ Создание поста отменено.</i>", reply_markup=get_main_reply_keyboard())
    await state.clear()

@router.message(F.text == "➡️ Пропустить", UserState.submit_content)
async def skip_description(message: types.Message, state: FSMContext):
    await message.answer(
        "👌 <b>Окей, отправляем без текста.</b>\n<i>Подтверждаешь?</i>",
        reply_markup=get_confirm_kb()
    )
    await state.set_state(UserState.confirm_sending)


@router.message(UserState.submit_content, F.text)
async def process_post_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("current_post_id")
    
    if not post_id:
        await message.answer(
    "⚠️ <b>Упс, данные потерялись.</b>\n"
    "<i>Пожалуйста, отправьте фото ещё раз.</i>"
)
        await state.clear()
        return

    async with async_session_maker() as session:
        post = await session.get(Post, post_id)
        if post:
            post.caption = message.text
            await session.commit()

    safe_caption = html.quote(message.text)
    await message.answer(
        f"📝 <b>Описание принято:</b>\n"
        f"<i>{safe_caption}</i>\n\n"
        f"🚀 <b>Всё верно? Отправляем?</b>",
        reply_markup=get_confirm_kb()
    )
    await state.set_state(UserState.confirm_sending)

@router.message(UserState.confirm_sending, F.text == "🚀 Отправить")
async def confirm_and_send(message: types.Message, state: FSMContext):

    data = await state.get_data()
    post_id = data.get("current_post_id")
    
    if not post_id:
        await message.answer("<i>Ошибка. Пост не найден.</i>")
        await state.clear()
        return
    status_msg = await message.answer("⏳ <b>Отправляю пост...</b>\n<i>Пожалуйста, подождите.</i>", reply_markup=None)

    async with ChatActionSender.upload_photo(chat_id=message.chat.id, bot=message.bot, initial_sleep=0):
        
        async with async_session_maker() as session:
            post = await session.get(Post, post_id)
            if post:
                post.status = "pending"
                await session.commit()
                success = await send_post_to_moderation(message.bot, post_id)
                try:
                    await status_msg.delete()
                except:
                    pass

                if success:
                    await message.answer(
                        f"✅ <b>Пост #{post_id} успешно отправлен!</b>\n<i>Спасибо, что присылаете контент! 😌</i>",
                        reply_markup=get_main_reply_keyboard()
                    )
                else:
                    await message.answer(
                        "<i>❌ Произошла ошибка при отправке админам.</i>", 
                        reply_markup=get_main_reply_keyboard()
                    )
            else:
                try:
                    await status_msg.delete()
                except:
                    pass
                await message.answer("Пост не найден в базе.", reply_markup=get_main_reply_keyboard())

    await state.clear()