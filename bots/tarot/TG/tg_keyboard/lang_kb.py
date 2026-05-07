from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from TG.tg_keyboard.callback_data_for_kb import lang_cbd_uni

lang_kb = InlineKeyboardMarkup(row_width=1, resize_keyboard=True)

en_button = InlineKeyboardButton(text="English", callback_data=lang_cbd_uni.new("en"))
lang_kb.insert(en_button)

fr_button = InlineKeyboardButton(text="Francais", callback_data=lang_cbd_uni.new("fr"))
lang_kb.insert(fr_button)

uk_button = InlineKeyboardButton(text="Українська", callback_data=lang_cbd_uni.new("uk"))
lang_kb.insert(uk_button)

ru_button = InlineKeyboardButton(text="Русский", callback_data=lang_cbd_uni.new("ru"))
lang_kb.insert(ru_button)
