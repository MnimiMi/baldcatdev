from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from TG.api_client import get_user, get_string, email_exists, email_linked, set_weblogin
from TG.context_taro import Context


async def check_web_login_request(message: types.Message):
    user_data = await get_user(message.from_user.id)
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(InlineKeyboardButton(text="Cancel ✖", callback_data="cancel"))
    await message.answer(
        await get_string("CHECK_WEB", user_data.get('lang', 'en')),
        reply_markup=keyboard
    )
    await Context.check_web.set()


async def check_web_login(message: types.Message, state: FSMContext):
    email = message.text.strip()
    user_id = message.from_user.id
    user_data = await get_user(user_id)
    lang = user_data.get('lang', 'en')

    if not await email_exists(email):
        msg_key = "CHECK_WEB_ERROR"
    elif await email_linked(email):
        msg_key = "EXIST_EMAIL"
    else:
        await set_weblogin(user_id, email)
        msg_key = "CHECK_WEB_SUCCESS"

    await message.answer(await get_string(msg_key, lang))
    await state.finish()


def check_web_handler(dp: Dispatcher):
    dp.register_message_handler(check_web_login_request, Command("bound_email"), state="*")
    dp.register_message_handler(check_web_login, state=Context.check_web)
