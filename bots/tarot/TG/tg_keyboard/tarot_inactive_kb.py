from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from TG.tg_keyboard.callback_data_for_kb import daily_card_inactive, choice_quantity

tarot_inactive_kb = InlineKeyboardMarkup(row_width=1, resize_keyboard=True)

inactive_button = InlineKeyboardButton(text="inactive", callback_data=daily_card_inactive.new())
tarot_inactive_kb.insert(inactive_button)

five_button = InlineKeyboardButton(text="3", callback_data=choice_quantity.new(3))
tarot_inactive_kb.insert(five_button)
