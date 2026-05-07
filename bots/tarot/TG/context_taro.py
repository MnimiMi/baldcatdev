from aiogram.dispatcher.filters.state import State, StatesGroup


class Context(StatesGroup):
    card_quantity = State()
    lang_choice_context = State()
    user_session = State()
    w_request = State()
    check_web = State()
    q_review = State()
    personal_reading = State()
