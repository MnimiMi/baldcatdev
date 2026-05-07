import re

from aiogram import Dispatcher, types
from aiogram.dispatcher import filters
from aiogram.dispatcher.filters import ChatTypeFilter

from TG.config import TELEGRAM_SUPPORT_CHAT_ID, REPLY_TO_THIS_MESSAGE, WRONG_REPLY


async def forward_to_chat(message: types.Message):
    bot = message.bot
    await bot.forward_message(TELEGRAM_SUPPORT_CHAT_ID, message.chat.id, message.message_id)


# @dp.message_handler(ChatTypeFilter(chat_type=types.ChatType.GROUP) & filters.IsReplyFilter)
async def forward_to_user(message: types.Message):
    bot = message.bot
    user_id = get_user_id_from_support_reply(message.reply_to_message)
    if user_id:
        await bot.copy_message(
            user_id,
            TELEGRAM_SUPPORT_CHAT_ID,
            message.message_id
        )
    else:
        await bot.send_message(
            TELEGRAM_SUPPORT_CHAT_ID,
            WRONG_REPLY
        )


def get_user_id_from_support_reply(reply_message: types.Message):
    if reply_message.forward_from:
        return reply_message.forward_from.id
    if not reply_message.text:
        return None

    if REPLY_TO_THIS_MESSAGE in reply_message.text:
        try:
            return int(reply_message.text.split('\n')[0])
        except ValueError:
            return None

    id_match = re.search(r"(?:Connected id:|\()(\d{5,})", reply_message.text)
    if id_match:
        return int(id_match.group(1))

    return None


def reg_handlers_sup(dp: Dispatcher):

    dp.register_message_handler(
        forward_to_user,
        ChatTypeFilter(chat_type=[types.ChatType.GROUP, types.ChatType.SUPERGROUP]) & filters.IsReplyFilter
    )
