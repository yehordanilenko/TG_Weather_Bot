from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from datetime import datetime
import requests
from config import open_weather_token
from database import add_or_update_user_in_db
from weather import send_weather_data, get_coordinates_for_city

class WeatherForm(StatesGroup):
    waiting_for_current_weather_city = State()
    waiting_for_subscribe_city_or_coordinates = State()
    waiting_for_city_selection = State()
    waiting_for_subscribe_time = State()

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start", "help"])
    dp.register_message_handler(curr_weather, commands=["current_weather"])
    dp.register_message_handler(current_weather_city_chosen, state=WeatherForm.waiting_for_current_weather_city)
    dp.register_callback_query_handler(handle_city_selection, lambda c: c.data and c.data.startswith('city_'), state=WeatherForm.waiting_for_city_selection)
    dp.register_message_handler(subscribe_command, commands=["subscribe"], state="*")
    dp.register_message_handler(subscribe_city_or_coordinates_input, state=WeatherForm.waiting_for_subscribe_city_or_coordinates)
    dp.register_callback_query_handler(subscribe_city_selected, lambda c: c.data.startswith('subscribe_city_'), state=WeatherForm.waiting_for_city_selection)
    dp.register_message_handler(subscribe_time_input, state=WeatherForm.waiting_for_subscribe_time)

async def start_command(message: types.Message):
    await message.reply(
        "Привет! Я бот, который предоставляет информацию о погоде.\n"
        "Напиши мне /current_weather и я отправлю тебе текущую информацию о погоде.\n"
        "Или напиши /subscribe, чтобы подписаться на ежедневную рассылку погоды."
    )

async def curr_weather(message: types.Message):
    await WeatherForm.waiting_for_current_weather_city.set()
    await message.reply("Введите, пожалуйста, название города или координаты через запятую без пробелов(например: 20.50,60.32)")

async def current_weather_city_chosen(message: types.Message, state: FSMContext):
    input_text = message.text.strip()

    if ',' in input_text:
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
        url = f"http://api.openweathermap.org/data/2.5/find?q={input_text}&appid={open_weather_token}&type=like&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data['count'] > 0:
            if data['count'] == 1:
                await send_weather_data(data['list'][0], message)
                await state.finish()
            else:
                cities = data['list']
                keyboard = InlineKeyboardMarkup(row_width=2)

                for city in cities:
                    button_text = f"{city['name']}, {city['sys']['country']}"
                    callback_data = f"city_{city['id']}"
                    keyboard.insert(InlineKeyboardButton(button_text, callback_data=callback_data))

                await message.reply("Найдено несколько городов. Пожалуйста, выберите один:", reply_markup=keyboard)
                await WeatherForm.waiting_for_city_selection.set()
        else:
            await message.reply("Город не найден. Пожалуйста, проверьте ввод и попробуйте снова.")

async def handle_city_selection(callback_query: types.CallbackQuery, state: FSMContext):
    city_id = callback_query.data.split('_')[1]
    url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={open_weather_token}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        await send_weather_data(data, callback_query.message)
        await state.finish()
    else:
        await callback_query.message.reply("Произошла ошибка при получении данных о погоде для выбранного города.")

    await callback_query.answer()  # Закрыть уведомление о callback на стороне пользователя

async def subscribe_command(message: types.Message):
    await WeatherForm.waiting_for_subscribe_city_or_coordinates.set()
    await message.reply("Введите название города или координаты для подписки на погоду (например, 'Киев' или '50.45,30.52').")

async def subscribe_city_or_coordinates_input(message: types.Message, state: FSMContext):
    input_text = message.text.strip()
    if ',' in input_text:
        try:
            lat, lon = map(float, input_text.split(','))
            await state.update_data(subscribe_lat=lat, subscribe_lon=lon)
            await WeatherForm.next()
            await message.reply("В какое время вы хотели бы получать прогноз? Введите время в формате HH:MM.")
        except ValueError:
            await message.reply("Некорректный формат координат. Пожалуйста, попробуйте еще раз.")
    else:
        url = f"http://api.openweathermap.org/data/2.5/find?q={input_text}&appid={open_weather_token}&type=like&units=metric"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200 and data['count'] > 0:
            if data['count'] == 1:
                await state.update_data(subscribe_city=input_text)
                await WeatherForm.next()
                await message.reply("В какое время вы хотели бы получать прогноз? Введите время в формате HH:MM.")
            else:
                cities = data['list']
                keyboard = InlineKeyboardMarkup(row_width=2)
                for city in cities:
                    button_text = f"{city['name']}, {city['sys']['country']}"
                    callback_data = f"subscribe_city_{city['id']}"
                    keyboard.insert(InlineKeyboardButton(button_text, callback_data=callback_data))
                await message.reply("Найдено несколько городов. Пожалуйста, выберите один:", reply_markup=keyboard)
                await WeatherForm.waiting_for_city_selection.set()
        else:
            await message.reply("Город не найден. Пожалуйста, проверьте ввод и попробуйте снова.")

async def subscribe_city_selected(callback_query: types.CallbackQuery, state: FSMContext):
    city_id = callback_query.data.split('_')[2]
    url = f"http://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={open_weather_token}&units=metric"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200:
        city_name = data['name']
        await state.update_data(subscribe_city=city_name)
        await WeatherForm.waiting_for_subscribe_time.set()
        await callback_query.message.edit_text(f"Вы выбрали {city_name}. В какое время вы хотели бы получать прогноз? Введите время в формате HH:MM.")
    else:
        await callback_query.message.reply("Произошла ошибка при выборе города.")
    await callback_query.answer()

async def subscribe_time_input(message: types.Message, state: FSMContext):
    time_input = message.text.strip()
    try:
        valid_time = datetime.strptime(time_input, '%H:%M')
        await state.update_data(notification_time=time_input)

        user_data = await state.get_data()
        if len(user_data) == 2:
            city = user_data.get('subscribe_city', 'Неизвестно')
            r1 = requests.get(
                f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={open_weather_token}&units=metric"
            )
            data1 = r1.json()
            timezone = data1['timezone'] // 3600
        else:
            r1 = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?lat={user_data.get('subscribe_lat')}&lon={user_data.get('subscribe_lon')}&appid={open_weather_token}&units=metric"
            )
            data1 = r1.json()
            city = data1['name']
            timezone = data1['timezone'] // 3600
        user_id = message.from_user.id
        await add_or_update_user_in_db(user_id, city, timezone, time_input)
        await message.reply(f"Вы подписались на уведомления в {time_input}.")
        await state.finish()
    except ValueError:
        await message.reply("Время введено в некорректном формате. Пожалуйста, введите время в формате HH:MM.")
