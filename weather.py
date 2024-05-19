import requests
from datetime import datetime
import aiohttp
import pytz
from aiogram import types, Bot  # Импортируем Bot из aiogram
from config import open_weather_token

async def send_weather_data(weather_data, message: types.Message):
    city_name = weather_data['name']
    temp = weather_data['main']['temp']
    cloudiness = weather_data['clouds']['all']
    pressure = weather_data['main']['pressure']
    wind_speed = weather_data['wind']['speed']
    wind_direction = weather_data['wind']['deg']
    humidity = weather_data['main']['humidity']

    if 'rain' in weather_data and weather_data['rain'] is not None and '1h' in weather_data['rain']:
        precipitation = weather_data['rain']['1h']
    else:
        precipitation = 'нет данных'

    reply_message = (
        f"Погода в {city_name}:\n"
        f"Температура: {temp}°C\n"
        f"Облачность: {cloudiness}%\n"
        f"Осадки: {precipitation}\n"
        f"Давление: {pressure} hPa\n"
        f"Ветер: {wind_speed} м/с, направление {wind_direction}°\n"
        f"Влажность: {humidity}%\n"
    )

    await message.reply(reply_message)

async def get_coordinates_for_city(city_name):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={open_weather_token}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    return data[0]['lat'], data[0]['lon']
    return None, None

async def send_weather_forecast(bot: Bot, user_id: int, lat: float, lon: float, db_timezone_offset_hours: int):
    api_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&appid={open_weather_token}&units=metric"
    db_timezone = pytz.timezone("Etc/GMT%+d" % -db_timezone_offset_hours)

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                message = "Прогноз погоды на ближайшие 8 часов:\n"
                for hour_data in data['hourly'][:8]:
                    forecast_time = datetime.fromtimestamp(hour_data['dt'], tz=db_timezone).strftime('%H:%M')
                    temp = hour_data['temp']
                    description = hour_data['weather'][0]['description']
                    wind_speed = hour_data['wind_speed']
                    message += f"{forecast_time}: Температура {temp}°C, {description}, скорость ветра {wind_speed} м/с\n"
                await bot.send_message(user_id, message)
            else:
                error_message = "Ошибка при получении данных о погоде."
                await bot.send_message(user_id, error_message)
