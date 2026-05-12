import asyncio
import datetime
import logging
import os
import random
from io import BytesIO
from urllib.parse import quote

import aiohttp
from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, ChatTypeFilter
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.types import InputFile
from aiogram.utils.exceptions import BadRequest, InvalidHTTPUrlContent, RetryAfter

from TG import config
from TG.api_client import (
    draw as api_draw, get_user, save_lang, accept_rules as api_accept_rules,
    start_trial as api_start_trial, mark_daily, get_string as api_get_string,
    claim_tarot_draw, get_cached_file_id, save_cached_file_id, delete_cached_file_id,
    get_random_copy
)
from TG.config import TELEGRAM_SUPPORT_CHAT_ID
from TG.context_taro import Context
from TG.help_request import invite_otzuv, help_requests_handlers
from TG.tg_keyboard.callback_data_for_kb import (
    accept_rules, tarot_request, weather_request, rules_request,
    help_request, about_request, lang_request, help_button_request,
    rev_request, daily_card_inactive, choice_quantity, personal_tarot
)
from TG.tg_keyboard.lang_kb import lang_kb
from TG.weather.weather_main import show_weather, get_weather_icon

_TYPE_TO_PATH = {
    'image':        '/cards/image',
    'imean':        '/cards/meaning',
    'mean':         '/cards/mean',
    'mean_personal': '/cards/meaning_personal',
}
APPS_BASE = os.getenv('APPS_BASE_URL', 'https://apps.baldcat.dev')

_drawing_in_progress: set[tuple[int, int, int]] = set()
_users_with_active_draws: set[int] = set()
_MAX_SEND_RETRIES = 3


def _prepare_url(method: str, **kwargs) -> str:
    path = _TYPE_TO_PATH.get(method, f'/cards/{method}')
    url = f"{APPS_BASE}{path}?"
    for key, value in kwargs.items():
        if not value:
            value = 0
        url += f"{key}={quote(str(value), safe='')}&"
    return url + f"p={random.randint(1, 100)}"


async def _localize(key: str, lang: str) -> str:
    try:
        return await api_get_string(key, lang)
    except Exception:
        return key


def _build_card_cache_key(suit, value: int, orient: int) -> str:
    normalized_suit = 0 if suit in (None, 0) else suit
    return f"{normalized_suit}_{value}_{orient}"


async def start_command(message, state: FSMContext = None, user_data: dict = None):
    if state is not None:
        await state.finish()

    if type(message) is types.message.Message:
        user_id = message.chat.id
    else:
        user_id = message.from_user.id

    if user_data is None:
        user_data = await get_user(user_id)

    lang = user_data.get('lang', 'en')
    rules_accepted = user_data.get('rules_accepted', False)

    if not rules_accepted:
        await show_rules_keyboard(message, lang)
    else:
        weather_icon = get_weather_icon()
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton(await _localize("TAROT", lang), callback_data=tarot_request.new()),
            InlineKeyboardButton(f"{await _localize('WEATHER', lang)} {weather_icon}", callback_data=weather_request.new()),
            InlineKeyboardButton(await _localize("LANG", lang), callback_data=lang_request.new()),
            InlineKeyboardButton(await _localize("HELP", lang), callback_data=help_request.new()),
            InlineKeyboardButton(await _localize("ABOUT", lang), callback_data=about_request.new()),
            InlineKeyboardButton(await _localize("CANCEL_KB", lang), callback_data="cancel"),
        )
        await message.answer(await _localize("START_MESSAGE", lang), reply_markup=kb)


async def process_tarot_request(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    await callback_query.answer(await _localize("TAROT", user_data.get('lang', 'en')))
    await get_started(callback_query.message, user_data=user_data)


async def process_weather_request(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    await callback_query.answer(await _localize("WEATHER", user_data.get('lang', 'en')))
    await show_weather(callback_query.message, user_data=user_data)


async def process_lang_request(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    await callback_query.answer(await _localize("LANG", user_data.get('lang', 'en')))
    await set_language_command(callback_query.message, user_data=user_data)


async def process_help_request(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    lang = user_data.get('lang', 'en')
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(await _localize("HOW", lang), callback_data=help_button_request.new()),
        InlineKeyboardButton(await _localize("RULES_BT", lang), callback_data=rules_request.new()),
        InlineKeyboardButton(await _localize("CANCEL_KB", lang), callback_data="cancel"),
    )
    await callback_query.bot.send_message(
        chat_id=callback_query.from_user.id,
        text=await _localize("HELP", lang),
        reply_markup=kb
    )


async def process_help_button_request(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    await callback_query.message.answer(await _localize("HOW_TO", user_data.get('lang', 'en')))


async def process_rules_request(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    lang = user_data.get('lang', 'en')
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(await _localize("CANCEL_KB", lang), callback_data="cancel"))
    await callback_query.message.answer(await _localize("RULES_MESSAGE", lang), reply_markup=kb)


async def process_about_request(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    lang = user_data.get('lang', 'en')
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(await _localize("ABOUT_US", lang), callback_data=help_button_request.new()),
        InlineKeyboardButton(await _localize("REVIEW", lang), callback_data=rev_request.new()),
        InlineKeyboardButton(await _localize("CANCEL_KB", lang), callback_data="cancel"),
    )
    await callback_query.message.answer(await _localize("ABOUT", lang), reply_markup=kb)


async def on_about_click(callback_query: types.CallbackQuery):
    user_data = await get_user(callback_query['from'].id)
    await callback_query.message.answer(await _localize("ABOUT_MESSAGE", user_data.get('lang', 'en')))


async def process_review_button_request(callback_query: types.CallbackQuery):
    await invite_otzuv(callback_query)


async def show_rules_keyboard(message, lang: str):
    from TG.help_request import show_rules
    await show_rules(message)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(await _localize('ACCEPT', lang), callback_data=accept_rules.new()),
        InlineKeyboardButton("Cancel ✖", callback_data="cancel"),
    )
    await message.answer(await _localize('WELCOME_ON_KB', lang), reply_markup=kb)


async def catch_rules_confirm(callback_query: CallbackQuery):
    if "accept_rules" not in callback_query.data:
        return
    await callback_query.message.delete()
    user_id = callback_query.from_user.id
    user_data = await get_user(user_id)
    await api_accept_rules(user_id)
    lang = user_data.get('lang', 'en')
    await callback_query.message.answer(await _localize("RULES_ACCEPTED", lang))
    user_data['rules_accepted'] = True
    await get_started(callback_query.message, user_data=user_data)


async def set_language_command(message: types.Message, state: FSMContext = None, user_data: dict = None):
    if not user_data:
        user_data = await get_user(message.from_user.id)
    await message.answer(await _localize('LANG_CHOICE', user_data.get('lang', 'en')), reply_markup=lang_kb)
    if state is not None:
        await state.finish()


async def chosen_lang_upload(callback_query: CallbackQuery, state: FSMContext):
    lang = callback_query.data.split(':')[-1]
    user_id = callback_query.message.chat.id
    await save_lang(user_id, lang)
    await callback_query.answer(await _localize('LANG_CHANGE', lang), show_alert=True)
    await callback_query.message.delete()
    await state.finish()


async def ask_question_for_personal_tarot(callback_query: CallbackQuery):
    user_data = await get_user(callback_query.from_user.id)
    await callback_query.message.answer(await _localize("ASK_PERSONAL_TAROT", user_data.get('lang', 'en')))
    await Context.personal_reading.set()


async def personal_tarot_request(message: types.Message, state: FSMContext):
    user_data = await get_user(message.from_user.id)
    await state.finish()
    await make_reading(
        bot=message.bot,
        number_of_cards=1,
        message_from_user=message.text,
        _lang=user_data.get('lang', 'en'),
        chat_id=message.chat.id
    )


async def get_started(message, state: FSMContext = None, straight_to_cards: bool = False, user_data: dict = None):
    if type(message).__name__ == 'CallbackQuery':
        user_id = message['from'].id
    elif hasattr(message, 'from_user') and message.from_user:
        user_id = message.from_user.id
    else:
        user_id = message.chat.id

    if user_data is None:
        user_data = await get_user(user_id)

    lang = user_data.get('lang', 'en')

    if state is not None:
        await state.finish()

    if not straight_to_cards:
        if not user_data.get('rules_accepted'):
            await start_command(message, user_data=user_data)
            return

        trial_state = user_data.get('trial_state', 1)
        subscription = user_data.get('subscription', 0)

        if not subscription:
            from TG.payment import buy
            if trial_state == 3:
                pass
            elif trial_state == 2:
                await message.answer(await _localize("TRIAL_ENDED", lang))
                await buy(message, user_data=user_data)
                return
            else:
                kb = InlineKeyboardMarkup()
                kb.add(
                    InlineKeyboardButton(await _localize("START_TRIAL", lang), callback_data="start_trial"),
                    InlineKeyboardButton(await _localize("CANCEL_KB", lang), callback_data="cancel"),
                )
                await message.answer(await _localize("GIVEME", lang), reply_markup=kb)
                return

    daily = user_data.get('daily', {})
    text_inactive = await _localize("INACTIVE", lang)
    text_3 = await _localize("3_CARDS", lang)
    text_personal = await _localize("PERSONAL_KB", lang)
    text_daily = await _localize("DAILY_KB", lang)

    if not daily.get('allowed', True):
        timestamp = daily.get('timestamp')
        time_left = ''
        if timestamp:
            now = datetime.datetime.now()
            midnight = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time(0, 0))
            diff = midnight - now
            h, rem = divmod(max(0, int(diff.total_seconds())), 3600)
            m = rem // 60
            time_left = f" {h}h : {m}min"
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton(text_inactive, callback_data=daily_card_inactive.new()),
            InlineKeyboardButton(text_3, callback_data=choice_quantity.new(3)),
            InlineKeyboardButton(text_personal, callback_data=personal_tarot.new()),
            InlineKeyboardButton("Cancel ✖", callback_data="cancel"),
        )
        await message.answer(f"{await _localize('CARD_ACT', lang)}{time_left}", reply_markup=kb)
    else:
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton(text_daily, callback_data=choice_quantity.new(1)),
            InlineKeyboardButton(text_3, callback_data=choice_quantity.new(3)),
            InlineKeyboardButton(text_personal, callback_data=personal_tarot.new()),
            InlineKeyboardButton("Cancel ✖", callback_data="cancel"),
        )
        await message.answer(await _localize("GREETINGS", lang), reply_markup=kb)


async def get_card_quantity(callback_query: CallbackQuery, state: FSMContext = None):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.message_id
    draw_key = (user_id, chat_id, message_id)

    if user_id in _users_with_active_draws:
        try:
            user_data = await get_user(user_id)
            lang = user_data.get('lang', 'en')
            await callback_query.answer(await _localize("DRAW_IN_PROGRESS", lang), show_alert=True)
        except Exception:
            try:
                await callback_query.answer()
            except Exception:
                pass
        return

    if draw_key in _drawing_in_progress:
        try:
            await callback_query.answer()
        except Exception:
            pass
        return

    _drawing_in_progress.add(draw_key)
    _users_with_active_draws.add(user_id)

    try:
        await callback_query.answer()
        claim = await claim_tarot_draw(user_id, chat_id, message_id)
        if not claim.get("claimed"):
            _drawing_in_progress.discard(draw_key)
            _users_with_active_draws.discard(user_id)
            return
        await callback_query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        _drawing_in_progress.discard(draw_key)
        _users_with_active_draws.discard(user_id)
        return

    callback_data = callback_query.data
    if state is not None:
        await state.finish()
    if callback_data == "daily_card_inactive":
        _drawing_in_progress.discard(draw_key)
        return

    user_data = await get_user(user_id)
    lang = user_data.get('lang', 'en')
    number_of_cards = int(callback_query.data.split(":")[1])
    is_daily = number_of_cards == 1

    asyncio.create_task(
        _process_tarot_draw(
            bot=callback_query.bot,
            chat_id=chat_id,
            user_id=user_id,
            lang=lang,
            number_of_cards=number_of_cards,
            is_daily=is_daily,
            source_message=callback_query.message,
            draw_key=draw_key,
        )
    )


async def _process_tarot_draw(
    bot: Bot,
    chat_id: int,
    user_id: int,
    lang: str,
    number_of_cards: int,
    is_daily: bool,
    source_message: types.Message,
    draw_key: tuple[int, int, int],
):
    started_at = asyncio.get_running_loop().time()
    logging.info(
        "Starting tarot draw for user %s: cards=%s daily=%s chat=%s",
        user_id,
        number_of_cards,
        is_daily,
        chat_id,
    )
    try:
        if number_of_cards == 3 and not is_daily:
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=await get_random_copy("THREE_CARD_DRAW", lang),
                )
            except Exception:
                logging.exception("Failed to send three-card intro message for user %s", user_id)
        await make_reading(
            bot=bot,
            number_of_cards=number_of_cards,
            _lang=lang,
            _daily=1 if is_daily else 0,
            chat_id=chat_id,
        )
        if is_daily:
            await mark_daily(chat_id)
        await source_message.delete()
        elapsed = asyncio.get_running_loop().time() - started_at
        logging.info(
            "Completed tarot draw for user %s in %.2fs",
            user_id,
            elapsed,
        )
    except Exception:
        logging.exception("Failed to make tarot reading for user %s", user_id)
        await source_message.answer("Something went wrong while drawing the cards. Please try again.")
    finally:
        _drawing_in_progress.discard(draw_key)
        _users_with_active_draws.discard(user_id)


async def make_reading(
    bot: Bot,
    number_of_cards: int,
    _lang: str,
    _daily: int = 0,
    chat_id=None,
    message_from_user: str = None,
):
    draw_started_at = asyncio.get_running_loop().time()
    result = await api_draw(number_of_cards, _lang)
    if not result.get('success'):
        raise Exception("Draw failed")
    draw_elapsed = asyncio.get_running_loop().time() - draw_started_at
    logging.info(
        "api_draw completed in %.2fs for chat %s: cards=%s daily=%s",
        draw_elapsed,
        chat_id,
        number_of_cards,
        _daily,
    )

    cards = result['cards']
    contexts = ["past", "present", "future"]

    for i, card in enumerate(cards):
        _value = card['value']
        _suit = card['suit']
        _orient = card['orient']
        label = f"{card['value_name']} {card['suit_name']}"

        if not message_from_user:
            params = {
                'val': _value, 'suite': _suit, 'orient': _orient,
                'daily': _daily, 'lang': _lang,
            }

            def _cardcode(idx):
                s = 1 if not cards[idx].get('suit') else cards[idx]['suit']
                return f"{s}_{cards[idx]['value']}_{cards[idx]['orient']}"

            if i == 1:
                params['pst'] = _cardcode(0)
            if i == 2:
                params['pst'] = _cardcode(0)
                params['prs'] = _cardcode(1)

            url = _prepare_url('imean', **params)
        else:
            url = _prepare_url(
                'mean_personal', val=_value, suite=_suit,
                orient=_orient, context=message_from_user, lang=_lang
            )

        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton(
            await _localize("MEANING", _lang),
            web_app=WebAppInfo(url=url)
        ))

        card_code = _build_card_cache_key(_suit, _value, _orient)
        send_started_at = asyncio.get_running_loop().time()
        logging.info(
            "Sending card %s/%s to chat %s: code=%s label=%s",
            i + 1,
            len(cards),
            chat_id,
            card_code,
            label,
        )
        await send_tarot_photo(
            bot=bot,
            chat_id=chat_id,
            card_code=card_code,
            photo_url=_prepare_url('image', val=_value, suite=_suit, orient=_orient),
            caption=label,
            reply_markup=kb,
        )
        send_elapsed = asyncio.get_running_loop().time() - send_started_at
        logging.info(
            "Sent card %s/%s to chat %s in %.2fs: code=%s",
            i + 1,
            len(cards),
            chat_id,
            send_elapsed,
            card_code,
        )


async def _send_photo_with_retry(bot: Bot, chat_id, photo, caption: str, reply_markup):
    for attempt in range(1, _MAX_SEND_RETRIES + 1):
        try:
            return await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
        except RetryAfter as exc:
            retry_after = getattr(exc, "timeout", None) or getattr(exc, "retry_after", 1)
            logging.warning(
                "Telegram flood control for chat %s, retrying in %s seconds (attempt %s/%s)",
                chat_id,
                retry_after,
                attempt,
                _MAX_SEND_RETRIES,
            )
            if attempt == _MAX_SEND_RETRIES:
                raise
            await asyncio.sleep(retry_after)


def _extract_file_id(message: types.Message) -> str | None:
    if not message or not getattr(message, "photo", None):
        return None
    return message.photo[-1].file_id if message.photo else None


async def send_tarot_photo(bot: Bot, chat_id, card_code: str, photo_url: str, caption: str, reply_markup):
    cached_file_id = await get_cached_file_id(card_code)
    if cached_file_id:
        logging.info("Telegram file cache hit for %s", card_code)
        try:
            await _send_photo_with_retry(bot, chat_id, cached_file_id, caption, reply_markup)
            return
        except BadRequest:
            logging.warning("Telegram file cache invalid for %s, falling back to URL upload", card_code)
            await delete_cached_file_id(card_code)

    logging.info("Telegram file cache miss for %s", card_code)
    try:
        message = await _send_photo_with_retry(bot, chat_id, photo_url, caption, reply_markup)
    except InvalidHTTPUrlContent:
        logging.warning("Telegram could not fetch image URL, uploading directly: %s", photo_url)
        photo = await _download_as_input_file(photo_url)
        message = await _send_photo_with_retry(bot, chat_id, photo, caption, reply_markup)

    file_id = _extract_file_id(message)
    if file_id:
        await save_cached_file_id(card_code, file_id)


async def _download_as_input_file(url: str) -> InputFile:
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.read()
    buf = BytesIO(data)
    buf.name = "tarot_card.jpg"
    return InputFile(buf, filename=buf.name)


async def start_trial_handler(query: CallbackQuery):
    user_id = query.from_user.id
    user_data = await get_user(user_id)
    lang = user_data.get('lang', 'en')
    await api_start_trial(user_id)
    await query.message.edit_reply_markup()
    await query.message.answer(await _localize("TRIAL_ACTIVATED", lang))
    await query.bot.send_message(
        chat_id=TELEGRAM_SUPPORT_CHAT_ID,
        text=f"trial\n📞 Connected id:{user_id}."
    )
    await asyncio.sleep(1)
    user_data = await get_user(user_id)
    await get_started(query.message, straight_to_cards=True, user_data=user_data)


async def forward_to_context(message: types.Message):
    user_data = await get_user(message.from_user.id)
    await make_reading(
        bot=message.bot,
        number_of_cards=1,
        _lang=user_data.get('lang', 'en'),
        message_from_user=message.text, chat_id=message.chat.id
    )


def main_requests_handler(dp: Dispatcher):
    help_requests_handlers(dp)

    for cmd, cb in [('tarot', get_started), ('weather', show_weather),
                    ('start', start_command), ('language', set_language_command)]:
        dp.register_message_handler(cb, Command(cmd))

    callbacks = [
        {'text': 'weather', 'cb': process_weather_request},
        {'text': 'tarot', 'cb': process_tarot_request},
        {'text': 'lang', 'cb': process_lang_request},
        {'text': 'about', 'cb': process_about_request},
        {'text': 'help_button', 'cb': on_about_click},
        {'text': 'help', 'cb': process_help_button_request},
        {'text': 'start_trial', 'cb': start_trial_handler},
        {'text': 'rules', 'cb': process_rules_request},
        {'text': 'Review', 'cb': process_review_button_request},
        {'text': 'personal_tarot', 'cb': ask_question_for_personal_tarot},
    ]
    for item in callbacks:
        dp.register_callback_query_handler(item['cb'], text=item['text'])

    dp.register_callback_query_handler(get_card_quantity, text_contains="tarot_quantity:", state="*")
    dp.register_callback_query_handler(chosen_lang_upload, text_contains="lang:")
    dp.register_callback_query_handler(catch_rules_confirm, text_contains="accept_rules", state="*")
    dp.register_callback_query_handler(start_command, text_contains="cancel", state="*")
    dp.register_message_handler(personal_tarot_request, state=Context.personal_reading)
    dp.register_message_handler(
        forward_to_context,
        ChatTypeFilter(chat_type=types.ChatType.PRIVATE),
        content_types=['text'],
        state=None
    )


class UserManager:
    """Kept for compatibility with user_class.user_auth import."""
    @staticmethod
    def get_user_by_email(weblogin):
        return None
