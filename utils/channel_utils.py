from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument
from aiogram import html

from config import config
from database.models import Post, User

async def send_post_to_channel(bot: Bot, post: Post, author: User) -> int | None:

    if not config.CHANNEL_ID:
        print("❌ Ошибка: Не указан CHANNEL_ID в конфиге")
        return None
    
    post_caption = post.caption if post.caption else ""
    safe_caption = html.quote(post_caption)

    if config.BOT_USERNAME:
        bot_link = f"https://t.me/{config.BOT_USERNAME}?start=info_{author.user_id}"
        author_signature = f"\n👤<a href='{bot_link}'>{html.quote(author.full_name)}</a>"
    else:
        author_signature = f"\n👤{html.quote(author.full_name)}"

    full_caption = safe_caption + author_signature

    media_group = []

    for i, item in enumerate(post.media_content):
        media = None
        if item['type'] == 'photo':
            media = InputMediaPhoto(media=item['file_id'])
        elif item['type'] == 'video':
            media = InputMediaVideo(media=item['file_id'])
        elif item['type'] == 'document':
            media = InputMediaDocument(media=item['file_id'])
            
        if media:
            if i == 0:
                media.caption = full_caption
            media_group.append(media)

    try:
        sent_message = None
        
        if media_group:
            messages = await bot.send_media_group(chat_id=config.CHANNEL_ID, media=media_group)
            sent_message = messages[0]
        else:
            sent_message = await bot.send_message(chat_id=config.CHANNEL_ID, text=full_caption)
        return sent_message.message_id
        
    except Exception as e:
        print(f"❌ Ошибка публикации в канал: {e}")
        return None