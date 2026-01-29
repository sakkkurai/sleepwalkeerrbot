from aiogram import Router, types, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update

from database.core import async_session_maker
from database.models import User
from aiogram import html
from states import UserState
from datetime import datetime
from keyboards.inline import get_github_kb
from keyboards.reply import get_edit_profile_kb, get_main_reply_keyboard, get_back_to_menu_kb
from config import version

router = Router()
BOT_START_TIME = datetime.now()

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
                    
                    public_text = (
                        f"👤 <b>ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ {html.quote(target_user.full_name)}</b>\n"
                        f"➖➖➖➖➖➖➖➖\n"
                        f"🆔 <b>ID:</b> {target_user.user_id}\n"
                        f"🏷 <b>Юзернейм:</b> {username_text}\n"
                        f"📝 <b>О себе:</b> {html.quote(target_user.description or 'Не указано')}\n"
                        f"➖➖➖➖➖➖➖➖\n"
                        f"📅 <b>Регистрация:</b> {target_user.created_at.strftime('%d.%m.%Y')}"
                    )
                    await message.answer(public_text)
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

@router.message(F.chat.type == "private", Command("profile"))
@router.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    async with async_session_maker() as session:
        user = await session.get(User, message.from_user.id)

        if not user:
             return await message.answer("<i>⚠️ Ошибка профиля. Напишите /start </i>")
        
        desc = user.description if user.description else "Не заполнено"

        safe_name = html.quote(user.full_name)
        safe_desc = html.quote(desc)
        
        text = (
            f"👤 <b>ТВОЙ ПРОФИЛЬ</b>\n"
            f"➖➖➖➖➖➖➖➖\n"
            f"🆔 <b>ID</b>: {user.user_id}\n"
            f"🏷 <b>Имя:</b> {safe_name}\n"
            f"📝 <b>О себе:</b> {safe_desc}\n"
            f"➖➖➖➖➖➖➖➖\n"
            f"📅 <b>Регистрация:</b> {user.created_at.strftime('%d.%m.%Y')}\n\n\n"
            f"👇 <i>Воспользуйся кнопками ниже, если хочешь изменить профиль.</i>"
        )
        await message.answer(text, reply_markup=get_edit_profile_kb())

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