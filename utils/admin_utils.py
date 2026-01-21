from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from config import config
from database.core import async_session_maker
from database.models import User, Post
from keyboards.inline import get_admin_keyboard
from aiogram import html

async def send_post_to_moderation(bot: Bot, post_id: int):
    async with async_session_maker() as session:
        post = await session.get(Post, post_id)
        if not post:
            return False

        author = await session.get(User, post.user_id)
        
    media_group = []
    
    for item in post.media_content:
        if item['type'] == 'photo':
            media_group.append(InputMediaPhoto(media=item['file_id']))
        elif item['type'] == 'video':
            media_group.append(InputMediaVideo(media=item['file_id']))
        elif item['type'] == 'document':
            media_group.append(InputMediaDocument(media=item['file_id']))

    username = f"@{author.username}" if author.username else "нет юзернейма"
    author_name = html.quote(author.full_name)
    user_desc = html.quote(author.description) if author.description else "Не указано"
    caption = html.quote(post.caption) if post.caption else "(Без текста)"

    safe_author = html.quote(author_name)
    safe_username = html.quote(username)
    safe_desc = html.quote(user_desc)
    safe_caption = html.quote(caption)

    text = (
        f"<b>📝 НОВАЯ ПРЕДЛОЖКА!</b> #post_{post.id}\n\n"
        f"🆔 <b>ID:</b> <code>{author.user_id}</code>\n"
        f"👤 <b>Юзер:</b> {safe_author} ({safe_username})\n"
        f"📱 <b>Описание юзера:</b> {safe_desc}\n"
        f"📅 <b>Регистрация:</b> {author.created_at.strftime('%d.%m.%Y')}\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"📄 <b>Текст поста:</b>\n{safe_caption}"
    )

    try:
        if media_group:
            await bot.send_media_group(chat_id=config.MODERATION_CHAT_ID, media=media_group)
        
        await bot.send_message(
            chat_id=config.MODERATION_CHAT_ID,
            text=text,
            reply_markup=get_admin_keyboard(post_id)
        )
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при отправке админам: {e}")
        return False