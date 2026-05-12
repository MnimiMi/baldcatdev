from aiogram import types, Dispatcher
from aiogram.types import ContentType, InlineKeyboardMarkup, InlineKeyboardButton

from TG import config
from TG.api_client import get_user, get_string
from TG.config import TELEGRAM_SUPPORT_CHAT_ID


async def buy(message: types.Message, user_data: dict = None):
    if not user_data:
        user_data = await get_user(message.from_user.id)
    lang = user_data.get('lang', 'en')

    pay_amount = 200
    formatted_sum = "{:.2f}".format(pay_amount / 100)
    label = await get_string("PAYMENT", lang)
    price = types.LabeledPrice(label=label, amount=pay_amount)

    if config.TAROT_PAY_TOKEN.split(':')[1] == 'TEST':
        await message.answer("Тестовый платеж!")

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        text=await get_string("PAY", lang) + " £" + formatted_sum,
        pay=True
    ))
    await message.bot.send_invoice(
        message.chat.id,
        title=label,
        description="🃏🃏🃏",
        provider_token=config.TAROT_PAY_TOKEN,
        currency="GBP",
        photo_url="https://tell.guru/images/pay_picture.jpg",
        photo_width=416,
        photo_height=260,
        is_flexible=False,
        prices=[price],
        start_parameter="one-month-subscription",
        payload="test-invoice-payload",
        reply_markup=keyboard
    )


async def successful_payment(message: types.Message):
    user_id = message.from_user.id
    user_data = await get_user(user_id)
    await message.answer(await get_string("PAYMENT_SUCCESS", user_data.get('lang', 'en')))
    await message.bot.send_message(
        chat_id=TELEGRAM_SUPPORT_CHAT_ID,
        text=f"💳 Payment\n📞 Connected id:{user_id} {message.from_user.first_name}."
    )


async def pre_checkout_query_handler(query: types.PreCheckoutQuery):
    if query.total_amount == 200:
        await query.bot.answer_pre_checkout_query(query.id, ok=True)
    else:
        await query.bot.answer_pre_checkout_query(
            query.id, ok=False, error_message="Incorrect payment amount"
        )


def payment_handler(dp: Dispatcher):
    dp.register_message_handler(buy, commands=['buy'])
    dp.register_message_handler(successful_payment, content_types=ContentType.SUCCESSFUL_PAYMENT)
    dp.register_pre_checkout_query_handler(pre_checkout_query_handler)
