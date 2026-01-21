from aiogram.fsm.state import State, StatesGroup

class UserState(StatesGroup):
    set_description = State()
    set_username = State()
    submit_content = State()
    confirm_sending = State()
    send_msg_to_moderation = State()


class AdminState(StatesGroup):
    editing_caption = State()