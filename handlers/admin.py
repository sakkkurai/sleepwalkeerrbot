from aiogram import Router, F, Bot, types
from aiogram.filters import CommandObject, Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, FSInputFile
from aiogram.utils.chat_action import ChatActionSender
from sqlalchemy import select, update
from aiogram import html

from config import config
from database.core import async_session_maker
from database.models import User, Post
from keyboards.inline import AdminCallback
from datetime import datetime
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatAction
from utils.channel_utils import send_post_to_channel
import sys
import asyncio
import io
import os

router = Router()

@router.callback_query(AdminCallback.filter(F.action == "profile"))
async def admin_profile_handler(query: CallbackQuery, callback_data: AdminCallback):
    post_id = callback_data.post_id

    async with async_session_maker() as session:
        post = await session.get(Post, post_id)
        if not post:
            await query.answer("Пост не найден", show_alert=True)
            return

        author = await session.get(User, post.user_id)
        
    
    text = (
        f"🕵️‍♂️ ИНФО ОБ АВТОРЕ\n"
        f"➖➖➖➖➖➖➖\n"
        f"🆔 ID: {author.user_id}\n"
        f"🔗 Link: t.me/{author.username} | {author.username}\n"
        f"👤 Имя: {html.quote(author.full_name)}\n"
        f"📅 Рег: {author.created_at.strftime('%d.%m.%Y')}\n\n"
        f"📝 Био:\n{html.quote(author.description or 'Не указано')}"
    )
    
    await query.answer(text, show_alert=True)


@router.callback_query(AdminCallback.filter(F.action == "reject"))
async def admin_reject_handler(query: CallbackQuery, callback_data: AdminCallback, bot: Bot):
    post_id = callback_data.post_id

    async with async_session_maker() as session:
        post = await session.get(Post, post_id)
        if not post:
            await query.answer("Пост уже удален или не найден", show_alert=True)
            return
        
        post.status = "rejected"
        await session.commit()
        
        try:
            await bot.send_message(
                chat_id=post.user_id,
                text=f"😔 Ваш пост #{post_id} был отклонен модератором."
            )
        except:
            pass

    await query.message.edit_text(
        text=f"{query.message.html_text}\n\n🔴 <b>ОТКЛОНЕНО администратором {html.quote(query.from_user.full_name)}</b>",
        reply_markup=None
    )


@router.callback_query(AdminCallback.filter(F.action == "approve"))
async def admin_approve_handler(query: CallbackQuery, callback_data: AdminCallback, bot: Bot):
    post_id = callback_data.post_id

    async with async_session_maker() as session:
        post = await session.get(Post, post_id)
        if not post:
            await query.answer("Пост не найден", show_alert=True)
            return

        post.status = "approved"
        await session.commit()
        
        author = await session.get(User, post.user_id)
        
        channel_message_id = None
        if author:
            channel_message_id = await send_post_to_channel(bot, post, author)
        
        url_button = None
        if channel_message_id and config.CHANNEL_USERNAME:
            post_link = f"https://t.me/{config.CHANNEL_USERNAME}/{channel_message_id}"
            url_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↗️ Перейти к посту", url=post_link)]
            ])

        try:
            await bot.send_message(
                chat_id=post.user_id,
                text=f"🎉 Ваш пост #{post_id} опубликован в канале!",
                reply_markup=url_button
            )
        except:
            pass 

    await query.message.edit_text(
        text=f"{query.message.html_text}\n\n🟢 <b>ОПУБЛИКОВАНО администратором {html.quote(query.from_user.full_name)}</b>",
        reply_markup=url_button
    )


@router.callback_query(AdminCallback.filter(F.action == "ban_menu"))
async def admin_ban_confirm(query: CallbackQuery, callback_data: AdminCallback):
    post_id = callback_data.post_id
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💀 ДА, ЗАБАНИТЬ НАВСЕГДА", 
                callback_data=AdminCallback(action="confirm_ban", post_id=post_id).pack()
            )
        ],
        [
            InlineKeyboardButton(
                text="⬅️ Нет, отмена",
                callback_data=AdminCallback(action="cancel_ban", post_id=post_id).pack()
            )
        ]
    ])
        
    await query.message.edit_reply_markup(reply_markup=confirm_kb)


@router.callback_query(AdminCallback.filter(F.action == "cancel_ban"))
async def admin_ban_cancel(query: CallbackQuery, callback_data: AdminCallback):
    post_id = callback_data.post_id
    from keyboards.inline import get_admin_keyboard
    
    await query.message.edit_reply_markup(reply_markup=get_admin_keyboard(post_id))



@router.callback_query(AdminCallback.filter(F.action == "confirm_ban"))
async def admin_ban_execute(query: CallbackQuery, callback_data: AdminCallback, bot: Bot):
    post_id = callback_data.post_id
    
    async with async_session_maker() as session:
        post = await session.get(Post, post_id)
        if not post:
            await query.answer("♿ Пост не найден", show_alert=True)
            return

        user = await session.get(User, post.user_id)
        if user:
            user.is_banned = True 
            post.status = "rejected"
            await session.commit()
            
            try:
                await bot.send_message(user.user_id, "<b>⛔️ Вы были заблокированы в боте.</b>\nХотите обжаловать блокировку? Свяжитесь с администратором канала — ссылка в закрепе.")
            except:
                pass
            
            await query.message.edit_text(
                f"{query.message.html_text}\n\n🔨 <b>ПОЛЬЗОВАТЕЛЬ ЗАБАНЕН администратором {html.quote(query.from_user.full_name)}</b>",
                reply_markup=None
            )
            await query.answer("✅ Пользователь забанен!", show_alert=True)
        else:
            await query.answer("♿ Пользователь не найден", show_alert=True)


@router.message(Command("reply"))
async def cmd_admin_reply(message: types.Message, command: CommandObject, bot: Bot):
    if message.chat.id != config.MODERATION_CHAT_ID:
        message.answer("<b>⛔️ Ты не можешь использовать эту команду.</b>")
        return 

    if not command.args:
        await message.answer("<b>⚠️ Использование:</b> <code>/reply ID ТЕКСТ СООБЩЕНИЯ</code>")
        return

    try:
        args_split = command.args.split(maxsplit=1)
        
        if len(args_split) < 2:
            await message.answer("<b>⚠️ Вы забыли написать текст сообщения.</b>")
            return
            
        target_id = int(args_split[0])
        reply_text = args_split[1]

    except ValueError:
        await message.answer("<b>❌ ID должен быть числом.</b>")
        return

    async with async_session_maker() as session:
        user = await session.get(User, target_id)
        
        if not user:
            await message.answer("<b>❌ Пользователь с таким ID не найден в базе.</b>")
            return
            
        try:
            text_to_send = (
                f"📨 <b>Сообщение от администратора:</b>\n"
                f"<blockquote>{html.quote(reply_text)}</blockquote>\n\n"
                f"<i>👇🏻 Чтобы ответить, воспользуйся кнопкой ниже.</i>"
            )
            
            await bot.send_message(target_id, text_to_send)
            
            await message.answer(
                f"<i>✅ Сообщение отправлено пользователю <a href='tg://user?id={target_id}'>{html.quote(user.full_name)}</a>.</i>"
            )
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить сообщение (юзер заблокировал бота?)\nОшибка: {e}")



@router.message(Command("ban"))
async def cmd_manual_ban(message: types.Message, command: CommandObject, bot: Bot):
    if message.chat.id != config.MODERATION_CHAT_ID:
        await message.answer("<b>⛔️ Ты не можешь использовать эту команду.</b>")
        return 

    if not command.args:
        await message.answer("⚠️ Использование: <code>/ban ID_ПОЛЬЗОВАТЕЛЯ</code>")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer("<b>❌ ID должен быть числом.</b>")
        return

    async with async_session_maker() as session:

        user = await session.get(User, target_id)
        
        if not user:
            await message.answer("<b>❌ Пользователь не найден в базе.</b>")
            return

        if user.is_banned:
            await message.answer("<b>ℹ️ Пользователь уже и так в бане.</b>")
            return

        user.is_banned = True
        await session.commit()
        
        await message.answer(
            f"🔨 Пользователь <a href='tg://user?id={target_id}'>{html.quote(user.full_name)}</a> забанен."
        )
        try:
            await bot.send_message(user.user_id, "<b>⛔️ Вы были заблокированы в боте.</b>\nХотите обжаловать блокировку? Свяжитесь с администратором канала — ссылка в закрепе.")
        except:
            pass


@router.message(Command("unban"))
async def cmd_unban_user(message: types.Message, command: CommandObject, bot: Bot):
    if message.chat.id != config.MODERATION_CHAT_ID:
        await message.answer("<b>⛔️ Ты не можешь использовать эту команду.</b>")
        return 

    if not command.args:
        await message.answer("<i>⚠️ Использование:</i> <code>/unban ID_ПОЛЬЗОВАТЕЛЯ</code>")
        return

    try:
        target_id = int(command.args.strip())
    except ValueError:
        await message.answer("<b>❌ ID должен быть числом.</b>")
        return

    async with async_session_maker() as session:
        user = await session.get(User, target_id)
        
        if not user:
            await message.answer("<b>❌ Пользователь с таким ID не найден в базе.</b>")
            return

        if not user.is_banned:
            await message.answer("<b>ℹ️ Этот пользователь и так не забанен.</b>")
            return

        user.is_banned = False
        await session.commit()
        
        await message.answer(
            f"✅ Пользователь <a href='tg://user?id={target_id}'>{html.quote(user.full_name)}</a> разбанен!"
        )
        try:
            await bot.send_message(target_id, "✅ <b>Ваш аккаунт был разблокирован!</b>\nНе нарушайте!\n\n")
        except:
            pass

@router.message(Command("sh", "shell"))
async def cmd_shell(message: types.Message, command: CommandObject):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("<b>⛔️ Ты не можешь использовать эту команду.</b>")
        return

    cmd = command.args
    if not cmd:
        await message.answer("Введите команду, например: <code>/sh ls -la</code>")
        return

    await message.answer(f"⏳ Выполняю: <code>{html.quote(cmd)}</code>...")

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    
    output = stdout.decode().strip()
    error = stderr.decode().strip()

    text = ""
    if output:
        text += f"<b>Output:</b>\n<pre>{html.quote(output)}</pre>\n"
    if error:
        text += f"<b>Error:</b>\n<pre>{html.quote(error)}</pre>"
    
    if not text:
        text = "<i>(Команда выполнена без вывода)</i>"

    if len(text) > 4000:
        from aiogram.types import BufferedInputFile
        file = BufferedInputFile(text.encode(), filename="output.txt")
        await message.answer_document(file, caption="Вывод слишком длинный, вот файл.")
    else:
        await message.answer(text)

@router.message(Command("py", "python"))
async def cmd_exec_python(message: types.Message, command: CommandObject):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("<b>⛔️ Ты не можешь использовать эту команду.</b>")
        return

    code = command.args
    if not code:
        await message.answer("Напиши код, например: <code>/py print(2+2)</code>")
        return

    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()

    try:
        func_code = (
            "async def __ex():\n" +
            "\n".join(f"    {line}" for line in code.split("\n")) +
            "\n    return locals()"
        )
        
        local_vars = {
            "message": message,
            "bot": message.bot,
            "config": config,
            "os": os,
            "sys": sys,
        }
        
        exec(func_code, globals(), local_vars)
        await local_vars["__ex"]()
        
    except Exception as e:
        await message.answer(f"❌ <b>Ошибка:</b>\n<code>{html.quote(str(e))}</code>")
        return
    finally:
        sys.stdout = old_stdout

    output = redirected_output.getvalue()
    
    if output:
        if len(output) > 4000:
             await message.answer("Вывод слишком большой.")
        else:
             await message.answer(f"🐍 <b>Результат:</b>\n<pre>{html.quote(output)}</pre>")
    else:
        await message.answer("🐍 Код выполнен (вывода нет).")

@router.message(Command("clean_kb"))
async def clean_keyboard(message: types.Message):
    if message.chat.id != config.MODERATION_CHAT_ID:
        await message.answer("<b>⛔️ Ты не можешь использовать эту команду.</b>")
        return

    await message.answer(
        "<b>🖕🏻 Клавиатура удалена.</b>", 
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(Command("export_db"))
async def cmd_export_db(message: types.Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("<b>⛔️ Ты не можешь использовать эту команду.</b>")
        return

    db_url = config.DB_URL
        
    if ":///" in db_url:
        db_path = db_url.split(":///")[-1]
    else:
        db_path = db_url

    if not os.path.exists(db_path):
        await message.answer(
            f"❌ <b>Ошибка экспорта!</b>\n\n"
            f"Я смотрю в конфиг и вижу путь:\n<code>{db_path}</code>\n"
            f"Но файла там нет! 😱\n\n"
            f"<i>Текущий DB_URL:</i> {html.quote(db_url)}"
        )
        return

    try:
        status = await message.answer("<b>⏳ Загружаю базу данных...</b>")
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)

        async with ChatActionSender.upload_document(chat_id=message.chat.id, bot=message.bot, initial_sleep=0):
            backup_file = FSInputFile(db_path)
            
            await message.answer_document(
                backup_file,
                caption=(
                    f"📦 <b>Бэкап базы данных</b>\n"
                    f"🗄 <b>Источник:</b> .env\n"
                    f"📍 <b>Путь:</b> <code>{db_path}</code>\n"
                    f"📅 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                )
            )
            await status.delete()

    except Exception as e:
        await message.answer(f"❌ Не удалось отправить файл:\n<code>{e}</code>")