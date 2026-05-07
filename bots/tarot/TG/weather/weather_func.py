def temp_icon(temp: int):
    if temp >= 30:
        return "👙"  # Очень жарко
    if temp >= 25:
        return "🕶"  # Жарко
    if temp >= 20:
        return "👗"  # Тепло
    if temp >= 18:
        return "👒️"  # Немного тепло
    if temp >= 15:
        return "🧥"  # Прохладно
    if temp >= 10:
        return "🧣"  # Холодно
    if temp >= 0:
        return "🧤"  # Очень холодно
    if temp >= -10:
        return "⛄"  # Морозно
    return "❄️"  # Очень морозно


def moon_icon(moon_phase: str):
    """
    Возвращает соответствующий значок для текущей фазы луны.
    argument: moon_phase -- фаза луны (строка)
    returns: иконка
    """
    if moon_phase == "Full Moon":
        return "🌝"
    elif moon_phase == "New Moon":
        return "🌚"
    elif moon_phase == "Waxing Crescent":
        return "🌒"  # Растущий серп
    elif moon_phase == "Waning Crescent":
        return "🌘"  # Убывающий серп
    elif moon_phase == "First Quarter":
        return "🌓"
    elif moon_phase == "Last Quarter":
        return "🌗"
    elif moon_phase == "Waxing Gibbous":
        return "🌖"  # Растущая луна
    elif moon_phase == "Waning Gibbous":
        return "🌕"  # Убывающая луна
    else:
        return "🌙"  # Общий значок для других случаев


def weather_icon(desc: str):
    code_to_smile = {
        "Clear": "🌞",
        "Clouds": "☁",
        "Rain": "🌧",
        "Drizzle": "☔",
        "Thunderstorm": "⛈",
        "Snow": "❄",
        "Mist": "\U0001F32B",
        "Smoke": "😶‍🌫️",
        "Haze": "🌫",
        "Dust": "🌫",
        "Fog": "🌫",
        "Squall": "🌪",
        "Tornado": "🌪",
        "Showers": "🌦",
        "Patchy rain nearby": "🌦",
        "Moderate rain": "🌧",
        "Heavy rain": "🌧",
        "Light rain": "🌦",
        "Overcast": "☁",
        "Partly cloudy": "⛅",
        "Mostly cloudy": "☁",
        "Patchy rain": "🌦",
        "Patchy light rain with thunder": "⛈",
        "Overcast": "☁",
        "Partly cloudy": "⛅",
    }

    if desc not in code_to_smile:
        return "🌦"
    return code_to_smile[desc]
