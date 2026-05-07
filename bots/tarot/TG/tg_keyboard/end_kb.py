from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from TG.tg_keyboard.callback_data_for_kb import yes_1_request

end_kb = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
yes_button = InlineKeyboardButton(text="I guess so", callback_data=yes_1_request.new())
end_kb.insert(yes_button)

cancel_button = InlineKeyboardButton(text="Cancel", callback_data="cancel")
end_kb.insert(cancel_button)
