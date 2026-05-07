import datetime

import requests
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from TG.api_client import get_user, get_string
from TG.config import WEATHER_TOKEN
from TG.context_taro import Context
from TG.tg_keyboard.callback_data_for_kb import forecast_req
from TG.weather import weather_func

FOR_WEATHER_API = "http://api.weatherapi.com/v1/"
WEATHER_API_KEY = WEATHER_TOKEN


async def get_weather(message: types.Message, state: FSMContext):
    if message.location is None:
        data = await get_weather_data(message.text)
    else:
        data = await get_weather_data(lat=message.location.latitude, lon=message.location.longitude)

    if not data or "status" in data and not data["status"]:
        error_message = data.get('message', 'Unknown error')
        await message.answer(f"Could'nt find this place. Please try again or click /cancel: {error_message}")
        return

    user_data = await get_user(message.from_user.id)
    lang = user_data.get('lang', 'en')

    location = data["location"]
    city = location["name"]
    current_weather = data["current"]
    feels_like = round(current_weather["feelslike_c"])
    cur_temp = round(current_weather["temp_c"])
    weather_icon = weather_func.temp_icon(feels_like)
    weather_desc = current_weather.get("condition", {}).get("text", "")
    wd = weather_func.weather_icon(weather_desc)
    humidity = current_weather["humidity"]
    wind = current_weather["wind_kph"]
    lat = location["lat"]
    lon = location["lon"]

    r_forecast = requests.get(
        f"{FOR_WEATHER_API}forecast.json?key={WEATHER_API_KEY}&q={lat},{lon}&days=3"
    )
    data_forecast = r_forecast.json()

    if not data_forecast or "error" in data_forecast:
        return

    astro_data = data_forecast["forecast"]["forecastday"][0]["astro"]
    sunrise_timestamp = astro_data["sunrise"]
    sunset_timestamp = astro_data["sunset"]
    moon_phase = astro_data["moon_phase"]

    weather_forecast_message = ""
    for day in data_forecast.get('forecast', {}).get('forecastday', []):
        condition_text = day["day"]["condition"]["text"]
        forecast_day = weather_func.weather_icon(condition_text)
        day_temp = round(day["day"]["maxtemp_c"])
        night_temp = round(day["day"]["mintemp_c"])
        day_f = datetime.datetime.strptime(day["date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        one_day = (f"{day_f}: {forecast_day}\n{8 * ' '}"
                   f"{await get_string('DAY', lang)}: {day_temp}C°, "
                   f"{await get_string('NIGHT', lang)}: {night_temp}C°\n")
        weather_forecast_message += one_day

    await message.answer(
        f"***{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}***\n"
        f"{await get_string('TEMPERATURE', lang)}: {cur_temp}C° {wd}\n"
        f"{await get_string('FEELS_LIKE', lang)}: {feels_like}C° {weather_icon}\n"
        f"{await get_string('HUMIDITY', lang)} 💧: {humidity}%\n"
        f"{await get_string('WIND', lang)} 🌬 {wind} км/ч\n"
        f"{await get_string('SUNRISE', lang)} 🌅: {sunrise_timestamp}\n"
        f"{await get_string('SUNSET', lang)} 🌇: {sunset_timestamp}\n"
        f"{await get_string('MOON_PHASE', lang)} {weather_func.moon_icon(moon_phase)}\n",
        reply_markup=ReplyKeyboardRemove()
    )

    await state.update_data(ww=weather_forecast_message)
    await state.update_data(ww_city=city)

    keyboard = InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(
        InlineKeyboardButton(text=await get_string('3_DAYS', lang), callback_data=forecast_req.new()),
        InlineKeyboardButton(text=await get_string('CANCEL_KB', lang), callback_data="cancel")
    )
    await message.answer(f"{await get_string('FORECAST', lang)}?", reply_markup=keyboard)


async def get_weather_data(city: str = None, lon: str = None, lat: str = None) -> dict:
    if city is None and lon is None and lat is None:
        return {"status": False, "message": "No data provided"}

    if city:
        city_encoded = requests.utils.quote(city)
        req_for_api = f"{FOR_WEATHER_API}current.json?key={WEATHER_API_KEY}&q={city_encoded}&alerts=yes"
    else:
        req_for_api = f"{FOR_WEATHER_API}current.json?key={WEATHER_API_KEY}&q={lat},{lon}&alerts=yes"

    try:
        r = requests.get(req_for_api)
        data = r.json()
        if "alerts" in data and "alert" in data["alerts"] and data["alerts"]["alert"]:
            alerts_message = ""
            for alert in data["alerts"]["alert"]:
                alerts_message += f"Alert Date: {alert.get('date', 'No date')}\nDescription: {alert.get('description', 'No description')}\n\n"
            data["alerts_message"] = alerts_message
        if "location" not in data:
            return {"status": False, "message": "🙈"}
        return data
    except Exception as e:
        return {"status": False, "message": f"Error while requesting: {str(e)}"}


async def forecast_req_from_kb(call: CallbackQuery, state: FSMContext):
    await call.answer(cache_time=50)
    data = await state.get_data()
    weather_forecast_message = data.get("ww")
    user_data = await get_user(call.from_user.id)
    lang = user_data.get('lang', 'en')
    await call.message.answer(f"{str(weather_forecast_message)}\n{await get_string('NICE_DAY', lang)}")
    await state.finish()


async def show_weather(message: Message, user_data: dict = None):
    if not user_data:
        user_data = await get_user(message.from_user.id)
    lang = user_data.get('lang', 'en')

    txt_for_kb = await get_string("SHARE_BUTTON", lang)
    keyboard = (types.ReplyKeyboardMarkup(resize_keyboard=True)
                .add(types.KeyboardButton(txt_for_kb, request_location=True)))
    await message.answer(await get_string("SHARE_LOCATION", lang), reply_markup=keyboard)
    await Context.w_request.set()


def get_weather_icon():
    month = datetime.datetime.now().month
    if 3 <= month <= 5:
        return "🌷"
    elif 6 <= month <= 8:
        return "☀️"
    elif 9 <= month <= 11:
        return "🍂"
    else:
        return "❄️"


def reg_weather(dp: Dispatcher):
    dp.register_message_handler(get_weather, state=Context.w_request)
    dp.register_callback_query_handler(forecast_req_from_kb, text="Forecast", state=Context.w_request)
    dp.register_message_handler(get_weather, state=Context.w_request, content_types=['location'])
