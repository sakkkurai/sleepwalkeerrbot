from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_help_kb():
     return ReplyKeyboardMarkup(keyboard=[
          [KeyboardButton(text="❗ Правила для отправки постов")],
          [KeyboardButton(text="👨‍💻 Связаться с поддержкой")],
          [KeyboardButton(text="⬅️ Назад")]
     ],
          resize_keyboard=True
     )

def get_skip_cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➡️ Пропустить"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )

def get_confirm_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Отправить"), KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_back_kb():
          return ReplyKeyboardMarkup(keyboard=[
          [KeyboardButton(text="⬅️ Назад")]
     ],
          resize_keyboard=True
     )

def get_edit_profile_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Изменить имя")],
            [KeyboardButton(text="✏️ Изменить описание")],
            [KeyboardButton(text="⬅️ Назад")]
        ], resize_keyboard=True
    )

def get_back_to_menu_kb():
        return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Вернуться в меню")]
        ], resize_keyboard=True
    ) 

def get_main_reply_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Профиль"), 
                KeyboardButton(text="✝️ Нужна помощь!")
            ]
        ],
        resize_keyboard=True,
        is_persistent=True
    )
    return keyboard