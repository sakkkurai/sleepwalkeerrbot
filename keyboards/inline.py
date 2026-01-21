from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

class AdminCallback(CallbackData, prefix="admin"):
    action: str
    post_id: int


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
                url="https://github.com/svkkkurai/sleepwalkeerrbot"
            )
        ]
    ])