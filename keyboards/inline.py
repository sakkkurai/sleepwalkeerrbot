from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from config import config

class AdminCallback(CallbackData, prefix="admin"):
    action: str
    post_id: int

class AdminToggleCallback(CallbackData, prefix="admin_toggle"):
    user_id: int
    action: str

def get_profile_kb(target_user_id: int, target_is_admin: bool, viewer_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="📋 Посты пользователя",
                callback_data=f"user_posts_{target_user_id}"
            )
        ]
    ]

    if viewer_id == config.ADMIN_ID:
        if target_is_admin:
            keyboard.append([
                InlineKeyboardButton(
                    text="❌ Снять права админа",
                    callback_data=AdminToggleCallback(user_id=target_user_id, action="demote").pack()
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    text="👑 Назначить админом",
                    callback_data=AdminToggleCallback(user_id=target_user_id, action="promote").pack()
                )
            ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard(post_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅",
                    callback_data=AdminCallback(action="approve", post_id=post_id).pack()
                ),
                InlineKeyboardButton(
                    text="❌",
                    callback_data=AdminCallback(action="reject", post_id=post_id).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤",
                    callback_data=AdminCallback(action="profile", post_id=post_id).pack()
                ),

                InlineKeyboardButton(
                    text="🔨",
                    callback_data=AdminCallback(action="ban_menu", post_id=post_id).pack()
                )
            ]
        ])

def get_github_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🐈 Исходный код на GitHub",
                url="https://github.com/sakkkurai/sleepwalkeerrbot"
            )
        ]
    ])

def get_reply_to_moder_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(
            text="✍️ Ответить",
            callback_data="msg_from_support_reply"
            )
        ]
    ])
