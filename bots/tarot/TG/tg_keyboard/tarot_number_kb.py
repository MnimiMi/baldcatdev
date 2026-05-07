from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from TG.tg_keyboard.callback_data_for_kb import choice_quantity

tarot_number_kb = InlineKeyboardMarkup(row_width=1, resize_keyboard=True)

one_button = InlineKeyboardButton(text="1", callback_data=choice_quantity.new(quantity=1))
tarot_number_kb.insert(one_button)

five_button = InlineKeyboardButton(text="3", callback_data=choice_quantity.new(quantity=3))
tarot_number_kb.insert(five_button)
