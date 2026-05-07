from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from TG.api_client import get_user, get_string
from TG.config import TELEGRAM_SUPPORT_CHAT_ID, REPLY_TO_THIS_MESSAGE
from TG.context_taro import Context
from TG.tg_keyboard.callback_data_for_kb import help_button_request, rev_request


async def show_rules(message: Message, lang: str = None):
    if not lang:
        user_data = await get_user(message.from_user.id)
        lang = user_data.get('lang', 'en')
    await message.answer(await get_string("RULES_MESSAGE", lang))


async def cancel_foo(call: CallbackQuery):
    user_data = await get_user(call.from_user.id)
    lang = user_data.get('lang', 'en')
    await call.message.answer(await get_string("CANCEL", lang))
    await call.message.delete()
    state = Dispatcher.get_current().current_state()
    await state.finish()


async def invite_otzuv(call: CallbackQuery):
    await Context.q_review.set()
    user_data = await get_user(call.from_user.id)
    await call.answer(cache_time=50)
    await call.message.answer(await get_string("GET_REVIEW", user_data.get('lang', 'en')))
    await call.message.delete_reply_markup()
    await call.message.delete()


async def answer_q_review(message: types.Message, state: FSMContext):
    user_data = await get_user(message.from_user.id)
    lang = user_data.get('lang', 'en')
    answer = message.text
    await state.update_data(answer1=answer)

    await message.bot.send_message(
        chat_id=TELEGRAM_SUPPORT_CHAT_ID,
        text=f"{message.from_user.id}\n{REPLY_TO_THIS_MESSAGE}\nMade a review\nName: {message.from_user.first_name}\nText: {answer}"
    )
    await message.answer(await get_string("TNX_REVIEW", lang))
    await state.finish()


def help_requests_handlers(dp: Dispatcher):
    dp.register_message_handler(show_rules, Command("rules"), state="*")
    dp.register_message_handler(cancel_foo, Command("cancel"), state="*")
    dp.register_callback_query_handler(cancel_foo, text="cancel", state="*")
    dp.register_callback_query_handler(invite_otzuv, text="Review")
    dp.register_message_handler(answer_q_review, state=Context.q_review)
