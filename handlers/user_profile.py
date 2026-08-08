import math

from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update

from config import config
from database.core import async_session_maker
from database.models import Post, User
from aiogram import html
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from states import UserState
from datetime import datetime
from keyboards.inline import get_github_kb, get_profile_kb
from keyboards.reply import get_edit_profile_kb, get_main_reply_keyboard, get_back_to_menu_kb
from config import version

router = Router()
BOT_START_TIME = datetime.now()
POSTS_PER_PAGE = 5

@router.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)
        keyboard = get_main_reply_keyboard()
        is_new_user = False

        if not user:
            new_user = User(
                user_id=message.from_user.id,
                username=message.from_user.username,
                full_name=message.from_user.full_name
            )
            session.add(new_user)
            await session.commit()
            user = new_user
            is_new_user = True

        args = command.args
        if args and args.startswith("info_"):
            try:
                target_user_id = int(args.replace("info_", ""))
                target_user = await session.get(User, target_user_id)

                if target_user:
                    if is_new_user:
                        await message.answer(
                            "👋 <b>Привет!</b>\n\n"
                            "<i>Я — бот для предложки. Хочешь, чтобы твои фото попали в канал?</i> 📸\n\n"
                            "👇 <b>Всё просто:</b> <i>отправь мне фото или видео прямо в этот чат, и мы начнём!</i>",
                            reply_markup=keyboard
                        )

                    username_text = f"@{html.quote(target_user.username)}" if target_user.username else "Не указано"
                    admin_status = "\n<b><i>👮🏻 Пользователь является администратором сообщества.</i></b>" if target_user.is_admin else ""


                    public_text = (
                        f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ {html.quote(target_user.full_name)}</b>\n"
                        f"➖➖➖➖➖➖➖➖\n"
                        f"🆔 <b>ID:</b> {target_user.user_id}\n"
                        f"🏷 <b>Юзернейм:</b> {username_text}\n"
                        f"📝 <b>О себе:</b> {html.quote(target_user.description or 'Не указано')}\n"
                        f"➖➖➖➖➖➖➖➖\n"
                        f"📅 <b>Регистрация:</b> {target_user.created_at.strftime('%d.%m.%Y')}"
                        f"{admin_status}"
                    )

                    await message.answer(public_text, reply_markup=get_profile_kb(
                        target_user_id=target_user.user_id,
                        target_is_admin=target_user.is_admin,
                        viewer_id=message.from_user.id
                    ))
                else:
                    await message.answer("<i>❌ Пользователь не найден.</i>")

                return

            except ValueError:
                pass

        if is_new_user:
            await message.answer(
                "👋 <b>Привет!</b>\n\n"
                "<i>Я — бот для предложки. Хочешь, чтобы твои фото попали в канал?</i> 📸\n\n"
                "👇 <b>Всё просто:</b> <i>отправь мне фото или видео прямо в этот чат, и мы начнём!</i>",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "✌️ <b>С возвращением!</b>\n\n"
                "<i>Есть новый контент? Кидай его в этот чат. 🚀</i>",
                reply_markup=keyboard
            )


@router.callback_query(F.data.startswith("user_posts_"))
async def cb_user_posts(query: CallbackQuery):
    parts = query.data.split("_")
    user_id = int(parts[2])
    page = int(parts[3]) if len(parts) > 3 else 1

    text, kb, error = await get_user_posts_payload(user_id, page)
    if error:
        await query.answer(error, show_alert=True)
        return

    try:
        await query.message.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass

    await query.answer()

@router.message(Command("posts"))
@router.message(F.text == "📋 Мои посты")
async def cmd_posts(message: types.Message, command: CommandObject = None):
    target_user_id = message.from_user.id

    if command and command.args:
        args_clean = command.args.strip()
        if args_clean.isdigit():
            target_user_id = int(args_clean)

    text, kb, error = await get_user_posts_payload(target_user_id, page=1)
    if error:
        return await message.answer(f"<i>{error}</i>")

    await message.answer(text, reply_markup=kb)


async def get_user_posts_payload(user_id: int, page: int = 1):
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if not user:
            return None, None, "Пользователь не найден"

        result = await session.execute(
            select(Post)
            .where(Post.user_id == user_id, Post.status == "approved")
            .order_by(Post.created_at.desc())
        )
        posts = result.scalars().all()

    if not posts:
        custom_emoji = html.custom_emoji("😑", "5424990921202612579")
        return None, None, f"<i> {custom_emoji} У вас пока нет опубликованных постов. </i>"

    total_posts = len(posts)
    total_pages = math.ceil(total_posts / POSTS_PER_PAGE)

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    start_idx = (page - 1) * POSTS_PER_PAGE
    end_idx = start_idx + POSTS_PER_PAGE
    current_page_posts = posts[start_idx:end_idx]

    buttons = []
    for post in current_page_posts:
        btn_text = f"#{post.id} · {post.created_at.strftime('%d.%m.%Y')}"
        if post.channel_message_id:
            post_link = f"https://t.me/{config.CHANNEL_USERNAME}/{post.channel_message_id}"
            button = InlineKeyboardButton(text=btn_text, url=post_link)
        else:
            button = InlineKeyboardButton(text=f"{btn_text} · (нет ссылки)", callback_data="ignore")
        buttons.append([button])

    if total_pages > 1:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"user_posts_{user_id}_{page - 1}"))
        else:
            nav_buttons.append(InlineKeyboardButton(text="⛔️", callback_data="ignore"))

        nav_buttons.append(InlineKeyboardButton(text=f"• {page}/{total_pages} •", callback_data="ignore"))

        if page < total_pages:
            nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"user_posts_{user_id}_{page + 1}"))
        else:
            nav_buttons.append(InlineKeyboardButton(text="⛔️", callback_data="ignore"))

        buttons.append(nav_buttons)

    buttons.append([
        InlineKeyboardButton(text="👤 К профилю", callback_data=f"user_info_{user_id}")
    ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = f"📋 <b>Посты пользователя {html.quote(user.full_name)}</b> <i>(Стр. {page}/{total_pages})</i>:"

    return text, kb, None

@router.callback_query(F.data == "ignore")
async def cb_ignore(query: CallbackQuery):
    await query.answer()

@router.callback_query(F.data.startswith("user_info_"))
async def cb_user_info(query: CallbackQuery):
    target_user_id = int(query.data.replace("user_info_", ""))

    async with async_session_maker() as session:
        target_user = await session.get(User, target_user_id)
        if not target_user:
            await query.answer("Пользователь не найден", show_alert=True)
            return

        username_text = f"@{html.quote(target_user.username)}" if target_user.username else "Не указано"
        admin_status = "\n<b><i>👮🏻 Пользователь является администратором сообщества.</i></b>" if target_user.is_admin else ""

        public_text = (
            f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ {html.quote(target_user.full_name)}</b>\n"
            f"➖➖➖➖➖➖➖➖\n"
            f"🆔 <b>ID:</b> {target_user.user_id}\n"
            f"🏷 <b>Юзернейм:</b> {username_text}\n"
            f"📝 <b>О себе:</b> {html.quote(target_user.description or 'Не указано')}\n"
            f"➖➖➖➖➖➖➖➖\n"
            f"📅 <b>Регистрация:</b> {target_user.created_at.strftime('%d.%m.%Y')}"
            f"{admin_status}"
        )

        await query.message.edit_text(
            public_text,
            reply_markup=get_profile_kb(
                target_user_id=target_user.user_id,
                target_is_admin=target_user.is_admin,
                viewer_id=query.from_user.id
            )
        )

@router.message((F.text == "❌ Вернуться в меню") | (F.text == "⬅️ Назад"))
async def back_to_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("<i>😌 Вы вернулись в меню.</i>", reply_markup=get_main_reply_keyboard())

@router.message(Command("info"))
async def info(message: types.Message):
    text = (
            f"<b>ℹ️ Версия: {version}</b>\n"
            f"<b>🚀 Аптайм: {get_uptime_str()}</b>\n\n"
            f"<i>👇🏻 Ознакомиться с исходным кодом можно по ссылке ниже.</i>"
        )
    await message.answer(text, reply_markup=get_github_kb())


@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message, command: CommandObject = None):
    target_id = message.from_user.id
    if command and command.args and command.args.isdigit():
        target_id = int(command.args)

    async with async_session_maker() as session:
        user = await session.get(User, target_id)

        if not user:
             return await message.answer("<i>❌ Пользователь не найден.</i>")

        desc = user.description if user.description else "Не заполнено"

        safe_name = html.quote(user.full_name)
        admin_status = "\n<b><i>👮🏻 Пользователь является администратором сообщества.</i></b>" if user.is_admin else ""

        safe_desc = html.quote(desc)

        if user.user_id == message.from_user.id:
            text = (
                f"👤 <b>ТВОЙ ПРОФИЛЬ</b>\n"
                f"➖➖➖➖➖➖➖➖\n"
                f"🆔 <b>ID</b>: {user.user_id}\n"
                f"🏷 <b>Имя:</b> {safe_name}\n"
                f"📝 <b>О себе:</b> {safe_desc}\n"
                f"➖➖➖➖➖➖➖➖\n"
                f"📅 <b>Регистрация:</b> {user.created_at.strftime('%d.%m.%Y')}"
                f"{admin_status}\n\n\n"
                f"👇 <i>Воспользуйся кнопками ниже, если хочешь изменить профиль.</i>"
            )
            return await message.answer(text, reply_markup=get_edit_profile_kb())

        else:
            username_text = f"@{html.quote(user.username)}" if user.username else "Не указано"
            text = (
                f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ {safe_name}</b>\n"
                f"➖➖➖➖➖➖➖➖\n"
                f"🆔 <b>ID:</b> {user.user_id}\n"
                f"🏷 <b>Юзернейм:</b> {username_text}\n"
                f"📝 <b>О себе:</b> {safe_desc}\n"
                f"➖➖➖➖➖➖➖➖\n"
                f"📅 <b>Регистрация:</b> {user.created_at.strftime('%d.%m.%Y')}"
                f"{admin_status}"
            )
            return await message.answer(
                text,
                reply_markup=get_profile_kb(
                    target_user_id=user.user_id,
                    target_is_admin=user.is_admin,
                    viewer_id=message.from_user.id
                )
            )

@router.message(F.text == "👤 Изменить имя")
@router.message(F.chat.type == "private", Command("set_name"))
async def start_new_name(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>👤 Введи новое имя.</b>\n\n"
        "<i>Оно будет отображаться при публикации твоих постов.</i>", reply_markup=get_back_to_menu_kb()
    )
    await state.set_state(UserState.set_username)

@router.message(F.text == "✏️ Изменить описание")
@router.message(F.chat.type == "private", Command("set_desc"))
async def start_set_desc(message: types.Message, state: FSMContext):
    await message.answer(
    "✏️ <b>Напиши пару слов о себе.</b>\n\n"
    "<i>Это может быть твоё устройство, опыт съемки или город.</i>\n"
    "<i>Пример: iPhone 15 Pro, снимаю стрит-фото, Киев.</i>", reply_markup=get_back_to_menu_kb())
    await state.set_state(UserState.set_description)

@router.message(UserState.set_username)
async def process_username(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("❌ Пришлите текст.")
        return

    new_username = message.text

    if len(new_username) > 20:
        await message.answer("😭 Вы ввели слишком длинное имя!\n<i>Максимальное кол-во символов: 20</i>")
        return

    async with async_session_maker() as session:
        stmt = update(User).where(User.user_id == message.from_user.id).values(full_name=new_username)
        await session.execute(stmt)
        await session.commit()

    await message.answer(
        f"<b>✅ Имя обновлено!</b>\n\n<i>Теперь оно:</i>\n{html.quote(new_username)}",
        reply_markup=get_edit_profile_kb()
    )
    await state.clear()

@router.message(UserState.set_description)
async def process_description(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("<i>❌ Пришлите текст.</i>")
        return

    new_desc = message.text

    if len(new_desc) > 200:
        await message.answer("😭 Вы ввели слишком длинное описание!\n<i>Максимальное кол-во символов: 200</i>")
        return

    async with async_session_maker() as session:
        stmt = update(User).where(User.user_id == message.from_user.id).values(description=new_desc)
        await session.execute(stmt)
        await session.commit()

    await message.answer(
        f"<b>✅ Описание обновлено!</b>\n\n<i>Теперь оно:</i>\n{html.quote(new_desc)}",
        reply_markup=get_edit_profile_kb()
    )
    await state.clear()

def get_uptime_str():
    now = datetime.now()
    delta = now - BOT_START_TIME

    days = delta.days
    seconds = delta.seconds

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{days}д {hours}ч {minutes}м {secs}с"
