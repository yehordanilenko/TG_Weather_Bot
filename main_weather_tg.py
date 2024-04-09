from aiogram import Bot, types
import logging
from datetime import datetime, timezone
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from config import tg_bot_token, open_weather_token
import pymysql
from config import host, user, password, db_name
import aiomysql
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import requests
from datetime import datetime, timedelta
import pytz

db_config = {
    'host': host,
    'port': 3306,
    'user': user,
    'password': password,
    'db': db_name,
    'cursorclass': aiomysql.DictCursor,
    'autocommit': True
}


try:
    connection = pymysql.connect(
        host=host,
        port=3306,
        user=user,
        password=password,
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("succesfull connected")

    try:
        print("уже создана БД")
        # with connection.cursor() as cursor:
        #     cr_table_qr = "CREATE TABLE `users`(id int AUTO_INCREMENT, user_id INTEGER, city VARCHAR(255), timezone INTEGER, PRIMARY KEY (id))"
        #     cursor.execute(cr_table_qr)
        #     print("aTable created successful")
    finally:
        connection.close()
except Exception as ex:
    print("Connection refused...")
    print(ex)

bot = Bot(token=tg_bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
now = datetime.now(timezone.utc)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)




class WeatherForm(StatesGroup):
    waiting_for_current_weather_city = State()  # Состояние ожидания города для текущей погоды
    waiting_for_subscribe_city = State()  # Состояние ожидания города для подписки
    waiting_for_city_selection = State()
    waiting_for_subscribe_city_or_coordinates = State()
    waiting_for_subscribe_time = State()

subscriptions = {}  # Здесь мы будем хранить данные о подписках


@dp.message_handler(commands=["start", "help"])
async def start_command(message: types.Message):
    await message.reply(
        "Привет! Я бот, который предоставляет информацию о погоде.\n"
        "Напиши мне /current_weather и я отправлю тебе текущую информацию о погоде.\n"
        "Или напиши /subscribe, чтобы подписаться на ежедневную рассылку погоды."
    )


@dp.message_handler(commands=["current_weather"])
async def curr_weather(message: types.Message):
    logging.info("Handling /current_weather command")
    await WeatherForm.waiting_for_current_weather_city.set()
    await message.reply("Введите, пожалуйста, название города или координаты через запятую без пробелов(например: 20.50,60.32)")



@dp.message_handler(state=WeatherForm.waiting_for_current_weather_city)
async def current_weather_city_chosen(message: types.Message, state: FSMContext):
    input_text = message.text.strip()

    # Проверяем, содержит ли ввод запятую, что указывает на координаты
    if ',' in input_text:
        # Обрабатываем ввод как координаты
        try:
            lat, lon = map(float, input_text.split(','))
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={open_weather_token}&units=metric"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                await send_weather_data(data, message)
                await state.finish()
            else:
                await message.reply("Не удалось получить данные о погоде по этим координатам.")
        except ValueError:
            await message.reply("Некорректный формат координат. Используйте формат 'широта,долгота'. Пожалуйста, попробуйте еще раз.")
    else:
        # Обрабатываем ввод как название города
        url = f"http://api.openweathermap.org/data/2.5/find?q={input_text}&appid={open_weather_token}&type=like&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data['count'] > 0:
            if data['count'] == 1:
                # Только один город найден
                await send_weather_data(data['list'][0], message)
                await state.finish()
            else:
                # Несколько городов найдено
                cities = data['list']
                keyboard = InlineKeyboardMarkup(row_width=2)  # Создаем клавиатуру

                # Добавляем кнопку для каждого города
                for city in cities:
                    button_text = f"{city['name']}, {city['sys']['country']}"
                    callback_data = f"city_{city['id']}"  # Используем уникальный идентификатор города в качестве callback_data
                    keyboard.insert(InlineKeyboardButton(button_text, callback_data=callback_data))

                await message.reply("Найдено несколько городов. Пожалуйста, выберите один:", reply_markup=keyboard)
                # Устанавливаем состояние ожидания выбора города
                await WeatherForm.waiting_for_city_selection.set()
        else:
            await message.reply("Город не найден. Пожалуйста, проверьте ввод и попробуйте снова.")



@dp.callback_query_handler(lambda c: c.data and c.data.startswith('city_'), state=WeatherForm.waiting_for_city_selection)
async def handle_city_selection(callback_query: types.CallbackQuery, state: FSMContext):
    city_id = callback_query.data.split('_')[1]  # Получаем ID города из callback_data
    url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={open_weather_token}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        await send_weather_data(data, callback_query.message)
        await state.finish()
    else:
        await callback_query.message.reply("Произошла ошибка при получении данных о погоде для выбранного города.")


    await bot.answer_callback_query(callback_query.id)  # Закрыть уведомление о callback на стороне пользователя



# Обработчик команды подписки
@dp.message_handler(commands=["subscribe"], state="*")
async def subscribe_command(message: types.Message):
    await WeatherForm.waiting_for_subscribe_city_or_coordinates.set()
    await message.reply("Введите название города или координаты для подписки на погоду (например, 'Киев' или '50.45,30.52').")

# Обработчик ввода города или координат для подписки
@dp.message_handler(state=WeatherForm.waiting_for_subscribe_city_or_coordinates)
async def subscribe_city_or_coordinates_input(message: types.Message, state: FSMContext):
    input_text = message.text.strip()
    if ',' in input_text:  # Если это координаты
        try:
            # Обрабатываем координаты и переходим к следующему шагу
            lat, lon = map(float, input_text.split(','))
            await state.update_data(subscribe_lat=lat, subscribe_lon=lon)
            await WeatherForm.next()
            await message.reply("В какое время вы хотели бы получать прогноз? Введите время в формате HH:MM.")
        except ValueError:
            await message.reply("Некорректный формат координат. Пожалуйста, попробуйте еще раз.")
    else:  # Если это название города
        # Поиск города через API
        url = f"http://api.openweathermap.org/data/2.5/find?q={input_text}&appid={open_weather_token}&type=like&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data['count'] > 0:
            if data['count'] == 1:
                # Если найден один город, сохраняем его и переходим к выбору времени
                await state.update_data(subscribe_city=input_text)
                await WeatherForm.next()
                await message.reply("В какое время вы хотели бы получать прогноз? Введите время в формате HH:MM.")
            else:
                # Если найдено несколько городов, предлагаем выбор
                cities = data['list']
                keyboard = InlineKeyboardMarkup(row_width=2)
                for city in cities:
                    button_text = f"{city['name']}, {city['sys']['country']}"
                    callback_data = f"subscribe_city_{city['id']}"
                    keyboard.insert(InlineKeyboardButton(button_text, callback_data=callback_data))
                await message.reply("Найдено несколько городов. Пожалуйста, выберите один:", reply_markup=keyboard)
                # Переходим к состоянию ожидания выбора города из списка
                await WeatherForm.waiting_for_city_selection.set()
        else:
            await message.reply("Город не найден. Пожалуйста, проверьте ввод и попробуйте снова.")

# Обработчик для выбора города из списка
@dp.callback_query_handler(lambda c: c.data.startswith('subscribe_city_'), state=WeatherForm.waiting_for_city_selection)
async def subscribe_city_selected(callback_query: types.CallbackQuery, state: FSMContext):
    city_id = callback_query.data.split('_')[2]  # Получаем ID города из callback_data
    # Поиск информации о городе через API
    url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={open_weather_token}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        city_name = data['name']
        # Сохраняем выбранный город и переходим к выбору времени
        await state.update_data(subscribe_city=city_name)
        await WeatherForm.waiting_for_subscribe_time.set()
        await callback_query.message.edit_text(f"Вы выбрали {city_name}. В какое время вы хотели бы получать прогноз? Введите время в формате HH:MM.")
    else:
        await callback_query.message.reply("Произошла ошибка при выборе города.")
    await bot.answer_callback_query(callback_query.id)

from aiogram.dispatcher.filters.state import StatesGroup, State

# Определение класса состояний для подписки
class SubscribeForm(StatesGroup):
    city_or_coordinates = State()  # Шаг для ввода города или координат
    notification_time = State()  # Шаг для ввода времени уведомлений


@dp.message_handler(state=WeatherForm.waiting_for_subscribe_time)
async def subscribe_time_input(message: types.Message, state: FSMContext):
    time_input = message.text.strip()
    # Попытка преобразования введенного времени в объект datetime
    try:
        # Указываем формат ввода времени
        valid_time = datetime.strptime(time_input, '%H:%M')
        # Если преобразование успешно, сохраняем время подписки в формате HH:MM
        await state.update_data(notification_time=time_input)

        user_data = await state.get_data()
        if(len(user_data) == 2):
            city = user_data.get('subscribe_city', 'Неизвестно')
            r1 = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={open_weather_token}&units=metric"
            )
            data1 = r1.json();
            timezone=data1['timezone']//3600
        else:
            r1 = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={user_data.get('subscribe_lat')}&lon={user_data.get('subscribe_lon')}&appid={open_weather_token}&units=metric"
            )
            data1 = r1.json();
            city = data1['name']
            timezone = data1['timezone']//3600
        user_id = message.from_user.id  # Получаем user_id из сообщения
        await add_or_update_user_in_db(user_id, city, timezone, time_input)
        #city = user_data.get('subscribe_city', 'Неизвестно')  # Получаем город из сохраненных данных пользователя
        await message.reply(f"Вы подписались на уведомления в {time_input}.")
        await state.finish()
    except ValueError:
        # Если преобразование не удалось, отправляем сообщение об ошибке
        await message.reply("Время введено в некорректном формате. Пожалуйста, введите время в формате HH:MM.")
        # Вызываем функцию для добавления пользователя в БД



async def send_weather_data(weather_data, message: types.Message):
    # Дополнительные данные, которые вы хотите отправить
    id = message.forward_from_message_id
    city_name = weather_data['name']
    temp = weather_data['main']['temp']
    cloudiness = weather_data['clouds']['all']
    pressure = weather_data['main']['pressure']
    wind_speed = weather_data['wind']['speed']
    wind_direction = weather_data['wind']['deg']
    humidity = weather_data['main']['humidity']

    # Проверяем наличие данных об осадках
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




# Пример функции для отправки прогноза погоды с использованием One Call API
async def send_weather_forecast(user_id, city, db_timezone):
    # URL для запроса к API OpenWeather
    api_url = f"https://api.openweathermap.org/data/3.0/onecall?q={city}&exclude=current,minutely,daily&appid={open_weather_token}&units=metric"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url) as response:
            # Проверяем, успешно ли выполнен запрос
            if response.status == 200:
                data = await response.json()

                # Строим сообщение с прогнозом погоды
                message = "Прогноз погоды на ближайшие 8 часов:\n"
                for hour_data in data['hourly'][:8]:  # Берем данные только на 8 часов
                    time_of_forecast = datetime.fromtimestamp(hour_data['dt'], pytz.timezone(data['timezone'])).strftime('%H:%M')
                    temp = hour_data['temp']
                    description = hour_data['weather'][0]['description'].capitalize()
                    wind_speed = hour_data['wind_speed']

                    message += f"{time_of_forecast}: Температура {temp}°C, {description}, Ветер {wind_speed} м/с\n"

                # Отправляем сообщение пользователю
                await bot.send_message(user_id, message)
            else:
                await bot.send_message(user_id, "Не удалось получить данные о погоде. Пожалуйста, попробуйте позже.")


async def add_or_update_user_in_db(user_id, city, timezone,notification_time):
    async with aiomysql.create_pool(**db_config) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Попытка вставить новую запись или обновить существующую
                await cur.execute("""
                    INSERT INTO `users` (user_id, city, timezone, notification_time) 
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE city = VALUES(city), timezone = VALUES(timezone), notification_time = VALUES(notification_time)
                """, (user_id, city, timezone, notification_time))

                await conn.commit()

async def get_user_timezone(user_id):
    async with aiomysql.create_pool(**db_config) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT timezone FROM `users` WHERE user_id = %s", (user_id,))
                result = await cur.fetchone()
                return result[0] if result else None

import aiohttp




async def send_weather_forecast(user_id, lat, lon, db_timezone_offset_hours):
    api_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&appid={open_weather_token}&units=metric"
    db_timezone = timezone(timedelta(hours=db_timezone_offset_hours))

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



async def get_coordinates_for_city(city_name):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={open_weather_token}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    return data[0]['lat'], data[0]['lon']
    return None, None







async def scheduler():
    while True:
        utc_now = datetime.now(pytz.utc)
        async with aiomysql.create_pool(**db_config) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute("SELECT user_id, city, timezone, notification_time FROM `users`")
                    users = await cur.fetchall()
                    for user in users:
                        user_id = user['user_id']
                        city = user['city']
                        db_timezone = user['timezone']
                        notification_delta = user['notification_time']  # Received as timedelta

                        # Получаем координаты для города
                        lat, lon = await get_coordinates_for_city(city)
                        if lat is None or lon is None:
                            print(f"Не удалось получить координаты для города: {city}")
                            continue

                        base_date = datetime(2000, 1, 1)  # Arbitrary base date
                        notification_time = (base_date + notification_delta).time()

                        user_local_time = (utc_now + timedelta(hours=db_timezone)).time()

                        if user_local_time.strftime('%H:%M') == notification_time.strftime('%H:%M'):
                            await send_weather_forecast(user_id, lat, lon, db_timezone)
                        else:
                            print(
                                f"Not time yet for user {user_id}: {notification_time.strftime('%H:%M')} != {user_local_time.strftime('%H:%M')}")
        await asyncio.sleep(60)



async def start_bot_and_scheduler():
    # Create a task for the scheduler function
    asyncio.create_task(scheduler())
    # Start polling (aiogram 2.12 and newer do not require passing the loop)
    await dp.start_polling()

if __name__ == '__main__':
    # Run the combined start function
    asyncio.run(start_bot_and_scheduler())