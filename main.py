import asyncio
import datetime
from datetime import *
import logging
import sys
import sqlite3
import uuid
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, Chat, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, InputMediaVideo, \
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import initialization
initialization.createcfg()
import config
import messages
import os
import platform
import psutil
import time


import sqlite3

class DatabaseHandler:
    def __init__(self, db_name='bot_db.sqlite'):
        self.db_name = db_name

    def create_media_groups_table(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_groups (
                id TEXT PRIMARY KEY,
                user_id INTEGER,
                description TEXT,
                message_id INTEGER
            )
        ''')

        conn.commit()
        conn.close()

    def add_message_id_column(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(media_groups);")
        columns = [col[1] for col in cursor.fetchall()]
        if "message_id" not in columns:
            cursor.execute('ALTER TABLE media_groups ADD COLUMN message_id INTEGER;')

        conn.commit()
        conn.close()

db_handler = DatabaseHandler()


db_handler.create_media_groups_table()
db_handler.add_message_id_column()



logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

storage = MemoryStorage()
bot = Bot(token=config.TOKEN)
dp = Dispatcher(storage=storage)
logger = logging.getLogger(__name__)

send = KeyboardButton(text="📸 Отправить")
send_addmore = KeyboardButton(text="➕ Добавить еще")
send_next = KeyboardButton(text="⏭ Дальше")
desc_skip = KeyboardButton(text="⏭ Пропустить")
needhelp = KeyboardButton(text="‼ Нужна помощь")
menu = KeyboardButton(text="❌ Вернуться в меню")
help_withpost = KeyboardButton(text="❗Правила постов")
help_connect = KeyboardButton(text="👤Связаться с модератором")
help_botinfo_github = InlineKeyboardButton(text="GitHub", url="https://github.com/svkkkurai/sleepwalkeerrbot")
shutdown_button = InlineKeyboardButton(text="❗Завершить сессию", callback_data="shutdown")
discard = InlineKeyboardButton(text="❌Отменить", callback_data="discard")

shutdown_markup = InlineKeyboardMarkup(inline_keyboard=[[shutdown_button, discard]])

github_markup = InlineKeyboardMarkup(inline_keyboard=[[help_botinfo_github]])

main_markup = ReplyKeyboardMarkup(
    keyboard=[[send, needhelp]],
    resize_keyboard=True
)

cancel_markup = ReplyKeyboardMarkup(
    keyboard=[[menu]],
    resize_keyboard=True
)

help_markup = ReplyKeyboardMarkup(
    keyboard=[[help_withpost, help_connect, menu]],
    resize_keyboard=True
)

add_more_markup = ReplyKeyboardMarkup(
    keyboard=[[send_next, menu]],
    resize_keyboard=True
)

add_desc_markup = ReplyKeyboardMarkup(
    keyboard=[[desc_skip, menu]],
    resize_keyboard=True
)

class UserStates(StatesGroup):
    waiting_photo_or_video = State()
    waiting_media = State()
    waiting_more_media = State()
    waiting_description = State()
    waiting_message_to_moderator = State()

def init_db():
    conn = sqlite3.connect('bot_db.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_groups (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            description TEXT,
            message_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS media_files (
            group_id TEXT,
            file_id TEXT,
            type TEXT,
            FOREIGN KEY(group_id) REFERENCES media_groups(id)
        )
    ''')
    conn.commit()
    return conn

def update_db_schema():
    conn = sqlite3.connect('bot_db.sqlite')
    cursor = conn.cursor()
    # Проверка наличия столбца message_id в таблице media_groups
    cursor.execute("PRAGMA table_info(media_groups);")
    columns = [col[1] for col in cursor.fetchall()]
    if "message_id" not in columns:
        cursor.execute('ALTER TABLE media_groups ADD COLUMN message_id INTEGER;')
    conn.commit()
    conn.close()

update_db_schema()

db_conn = init_db()

async def get_channel_info(bot: Bot, chat_id: int):
    try:
        chat: Chat = await bot.get_chat(chat_id)
        title = chat.title
        invite_link = chat.invite_link if chat.invite_link else f"https://t.me/{chat.username}"
        return title, invite_link
    except Exception as e:
        logging.error(f"Error getting channel info: {e}")
        return None, None

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    title, link = await get_channel_info(bot, config.CHANNEL_ID)
    if title:
        await message.reply(
            f"❤Привет! Я - бот-предложка для канала [{title}]({link}). С помощью меня ты сможешь предложить свой пост!"
            f"\nℹ️Воспользуйся нижней клавиатурой для управления ботом.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_markup,
            disable_web_page_preview=True
        )
    else:
        await message.reply(
            "Упс.. Ошибка! Не удалось получить информацию о канале."
        )
    await state.clear()


@dp.message(Command("myid"))
async def my_id_command(message: Message):
    await message.reply(f"Your Telegram ID: {message.from_user.id}", parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("sysinfo"))
async def sysinfo(message: Message):
    user_name = os.getlogin()
    os_name = platform.system() + " " + platform.release()
    build_version = platform.version()
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_struct = time.gmtime(uptime_seconds)
    uptime = f"{uptime_struct.tm_yday - 1} days, {uptime_struct.tm_hour} hours, {uptime_struct.tm_min} minutes"
    screen_resolution = "1920x1080 @60Hz"
    cpu_info = platform.processor()
    gpu_info = "Intel(R) UHD Graphics"

    # Информация о памяти
    virtual_memory = psutil.virtual_memory()
    total_memory = virtual_memory.total // (1024 * 1024)
    used_memory = virtual_memory.used // (1024 * 1024)
    memory_usage_percentage = virtual_memory.percent

    # Информация о диске
    disk_usage = psutil.disk_usage('/')
    total_disk = disk_usage.total // (1024 * 1024 * 1024)
    free_disk = disk_usage.free // (1024 * 1024 * 1024)
    disk_usage_percentage = disk_usage.percent

    # Вывод информации
    await message.reply(
        f"<b>{user_name}@{platform.node()}</b>\n"
        f"--------------\n"
        f"<b>OS:</b> {os_name}\n"
        f"<b>Build:</b> {build_version}\n"
        f"<b>Uptime:</b> {uptime}\n"
        f"<b>Resolution:</b> {screen_resolution}\n" 
        f"<b>Terminal:</b> {os.environ.get('COMSPEC', 'cmd.exe')}\n"
        f"<b>CPU:</b> {cpu_info}\n"
        f"<b>GPU:</b> {gpu_info}\n"
        f"<b>Memory:</b> {used_memory} MB / {total_memory} MB ({memory_usage_percentage}% in use)\n"
        f"<b>Disk:</b> / {total_disk} GB ({free_disk} GB free)",
        parse_mode=ParseMode.HTML
    )

def fixmd(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)


@dp.message(Command("shutdown"))
async def shutdown(message: Message):
    if message.from_user.id == config.SENIOR_ADMIN:
        await message.reply("❗Вы точно хотите завершить работу системы?", reply_markup=shutdown_markup)
    else:
        await message.reply("💔Ваших прав недостаточно для выполнения этого действия.")


@dp.message(Command("bot_info"))
async def shutdown(message: Message):
    await message.reply(messages.help_botinfo, reply_markup=github_markup, parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("chat_id"))
async def chat_id_command(message: Message):
       await message.reply(f"Here's the data of chat.\nJSON: \n```\n{message.chat}```", parse_mode=ParseMode.MARKDOWN)


@dp.message(UserStates.waiting_media)
async def receive_first_media(message: Message, state: FSMContext):
    if message.text == menu.text:
        await message.reply("ℹ️Вы вернулись в меню.", reply_markup=main_markup)
        await state.clear()
    else:
        await process_media(message, state)
        await message.reply("✅Прикреплено к альбому.", reply_markup=add_more_markup)
        await state.set_state(UserStates.waiting_more_media)


@dp.message(UserStates.waiting_more_media)
async def receive_more_media(message: Message, state: FSMContext):
    if message.text == send_next.text:
        await message.reply("📝Пожалуйста, напишите описание для медиа файлов или нажмите «Пропустить».", reply_markup=add_desc_markup)
        await state.set_state(UserStates.waiting_description)
    elif message.text == menu.text:
        await message.reply("ℹ️Вы вернулись в меню.", reply_markup=main_markup)
        await state.clear()
    else:
        await process_media(message, state)
        await message.reply("ℹ️Воспользуйтесь кнопками внизу.", reply_markup=add_more_markup)

async def process_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_group = data.get("media_group", [])
    group_id = data.get("group_id")

    if not group_id:
        group_id = str(uuid.uuid4())
        await state.update_data(group_id=group_id)

    cursor = db_conn.cursor()
    if message.content_type == types.ContentType.PHOTO:
        file_id = message.photo[-1].file_id
        media_group.append(InputMediaPhoto(media=file_id))
        cursor.execute('INSERT INTO media_files (group_id, file_id, type) VALUES (?, ?, ?)', (group_id, file_id, 'photo'))
    elif message.content_type == types.ContentType.VIDEO:
        file_id = message.video.file_id
        media_group.append(InputMediaVideo(media=file_id))
        cursor.execute('INSERT INTO media_files (group_id, file_id, type) VALUES (?, ?, ?)', (group_id, file_id, 'video'))
    db_conn.commit()

    await state.update_data(media_group=media_group)

approve_button = InlineKeyboardButton(text="✅ Отправить", callback_data="approve")
reject_button = InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")
inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[approve_button, reject_button]])

@dp.message(UserStates.waiting_description)
async def receive_description(message: Message, state: FSMContext):
    if message.text == menu.text:
        await message.reply("ℹ️Вы вернулись в меню.", reply_markup=main_markup)
        await state.clear()
        return

    description = message.text if message.text != desc_skip.text else ""
    data = await state.get_data()
    group_id = data.get("group_id")

    cursor = db_conn.cursor()
    cursor.execute('INSERT INTO media_groups (id, user_id, description) VALUES (?, ?, ?)', (group_id, message.from_user.id, description))
    db_conn.commit()

    cursor.execute('SELECT file_id, type FROM media_files WHERE group_id = ?', (group_id,))
    files = cursor.fetchall()
    name = fixmd(message.from_user.full_name)
    media_group = []
    for i, (file_id, file_type) in enumerate(files):
        if file_type == 'photo':
            if i == len(files) - 1:
                media_group.append(InputMediaPhoto(media=file_id, caption=f"{description}\n👤[{name}](tg://user?id={message.from_user.id})", parse_mode=ParseMode.MARKDOWN_V2))
            else:
                media_group.append(InputMediaPhoto(media=file_id))
        elif file_type == 'video':
            if i == len(files) - 1:
                media_group.append(InputMediaVideo(media=file_id, caption=f"{description}\n👤[{name}](tg://user?id={message.from_user.id})", parse_mode=ParseMode.MARKDOWN_V2))
            else:
                media_group.append(InputMediaVideo(media=file_id))

    if media_group:
        sent_messages = await bot.send_media_group(config.MODER_CHAT_ID, media_group)

        # Сохранение message_id
        message_id = sent_messages[0].message_id
        cursor.execute('UPDATE media_groups SET message_id = ? WHERE id = ?', (message_id, group_id))
        db_conn.commit()

        # Отправляем сообщение с запросом на проверку
        await bot.send_message(
            config.MODER_CHAT_ID,
            text="Пожалуйста, одобрите или отклоните предложенный пост.",
            reply_markup=inline_keyboard,
            reply_to_message_id=message_id
        )

        await message.reply("✅Ваши файлы и описание были отправлены на проверку! Спасибо!")
        await bot.send_message(message.chat.id, text="ℹ️Вы вернулись в меню.", reply_markup=main_markup)
    else:
        await message.reply("❌Произошла ошибка при отправке медиа файлов.", reply_markup=main_markup)

    await state.clear()


@dp.callback_query(lambda c: c.data in ["approve", "reject"])
async def process_callback(callback_query: types.CallbackQuery):
    action = callback_query.data
    cursor = db_conn.cursor()

    logging.debug(f"callback_query.message.reply_to_message.message_id: {callback_query.message.reply_to_message.message_id}")

    cursor.execute('SELECT id FROM media_groups WHERE message_id = ?', (callback_query.message.reply_to_message.message_id,))
    result = cursor.fetchone()

    if result is None:
        await callback_query.answer("Ошибка: не удалось найти группу медиа файлов.")
        logging.error(f"Не удалось найти группу медиа файлов для message_id: {callback_query.message.reply_to_message.message_id}")
        return

    group_id = result[0]

    if action == "approve":
        cursor.execute('''
            SELECT media_files.file_id, media_files.type, media_groups.description, media_groups.user_id
            FROM media_files
            JOIN media_groups ON media_files.group_id = media_groups.id
            WHERE media_groups.id = ?
        ''', (group_id,))
        files = cursor.fetchall()

        user_id = files[0][3]
        user = await bot.get_chat(user_id)
        title, link = await get_channel_info(bot, config.CHANNEL_ID)

        media_group = []
        for i, (file_id, file_type, description, _) in enumerate(files):
            caption = f"{fixmd(description)}\n👤[{fixmd(user.full_name)}](tg://user?id={user.id})\n\n[Подписаться]({link}) \| [Отправить пост](tg://user?id=7412484247)" if i == len(files) - 1 else None
            if file_type == 'photo':
                media_group.append(InputMediaPhoto(media=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN_V2))
            elif file_type == 'video':
                media_group.append(InputMediaVideo(media=file_id, caption=caption, parse_mode=ParseMode.MARKDOWN_V2))

        if media_group:
            await bot.send_media_group(config.CHANNEL_ID, media_group)
        ftoday = date.today()
        today = ftoday.strftime('%d.%m.%Y')
        utc_vanilla = datetime.now(timezone.utc)
        UTC = utc_vanilla.strftime("%H:%M")
        name = fixmd(callback_query.from_user.full_name)
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"**✅ Пост отправлен\!**\n**👮🏻 Модератор \- ** [{name}](tg://user?id={callback_query.from_user.id})\n\n🕐 Действие модератора было сделано **{fixmd(today)}** в **{fixmd(UTC)}** по UTC",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=None
        )
    elif action == "reject":
        ftoday = date.today()
        today = ftoday.strftime('%d.%m.%Y')
        utc_vanilla = datetime.now(timezone.utc)
        UTC = utc_vanilla.strftime("%H:%M")
        name = fixmd(callback_query.from_user.full_name)

        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text=f"**❌ Пост отклонён\!**\n**👮🏻 Модератор \- ** [{name}](tg://user?id={callback_query.from_user.id})\n\n🕐 Действие модератора было сделано **{fixmd(today)}** в **{fixmd(UTC)}** по UTC",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=None
        )

        await callback_query.answer()

@dp.callback_query(lambda callback_query: callback_query.data in ["shutdown", "discard"])
async def handle_callback(callback_query: CallbackQuery):
    action = callback_query.data
    if action == "shutdown":
        await callback_query.message.edit_text("💢Выключаю систему...")
        if os.name == 'nt':
            os.system('shutdown /s /t 0')
        elif os.name == 'posix':
            os.system('sudo shutdown now')
    elif action == "discard":
            await callback_query.message.edit_text("❗Вы отменили завершение работы.")



user_moderator_map = {}

@dp.message(UserStates.waiting_message_to_moderator)
async def receive_message_to_moderator(message: Message, state: FSMContext):
    if message.text == menu.text:
        await message.reply("ℹ️Вы вернулись в меню.", reply_markup=main_markup)
        await state.clear()
    else:
        forwarded_message = await bot.forward_message(
            chat_id=config.MODER_CHAT_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        user_moderator_map[forwarded_message.message_id] = message.from_user.id
        await message.reply("*❗Ваше сообщение отправлено модератору.*\n\nУчтите, что для того, чтобы получить ответ вам нужно открыть профиль при пересылке в настройках конфиденциальности, и написать снова.", parse_mode=ParseMode.MARKDOWN)
        await state.clear()
        await bot.send_message(message.from_user.id, "ℹ️Вы вернулись в меню.", reply_markup=main_markup)

@dp.message(lambda message: message.reply_to_message and message.reply_to_message.forward_from)
async def handle_reply_from_moderator(message: Message):
    original_user_id = user_moderator_map.get(message.reply_to_message.message_id)
    if original_user_id:
        await bot.send_message(
            original_user_id,
            f"❗Ответ от модератора!\n`{message.text}`\n\nЧтобы ответить, перейдите в *«‼ Нужна помощь → Связаться с модератором»*",
            parse_mode=ParseMode.MARKDOWN
        )
        await message.reply("✅Ваше сообщение отправлено пользователю.")

@dp.message()
async def handle_buttons(message: Message, state: FSMContext):
    if message.text == "📸 Отправить":
        await state.clear()
        await state.set_state(UserStates.waiting_media)
        await message.reply("ℹ️Отправьте ваше фото!", reply_markup=cancel_markup)
    elif message.text == "‼ Нужна помощь":
        await message.reply("⁉С чем конкретно вам нужна помощь?", reply_markup=help_markup)
    elif message.text == "❗Правила постов":
        await message.reply(f"{messages.help_howtopost}", reply_markup=main_markup, parse_mode=ParseMode.MARKDOWN)
    elif message.text == "👤Связаться с модератором":
        await state.set_state(UserStates.waiting_message_to_moderator)
        await message.reply("⁉Напишите ваше сообщение или вернитесь в главное меню.", reply_markup=cancel_markup)
    elif message.text == "❌ Вернуться в меню":
        await message.reply("ℹ️Вы вернулись в меню.", reply_markup=main_markup)
        await state.clear()
    else:
        await bot.send_message(message.from_user.id, "ℹ️ Воспользуйтесь клавиатурой для навигации.", reply_markup=main_markup)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
