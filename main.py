import requests
from pprint import pprint
import datetime
from config import open_weather_token
import pymysql
from config import host, user, password, db_name


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
        with connection.cursor() as cursor:
            #cr_table_qr = "CREATE TABLE `users`(id int AUTO_INCREMENT, user_id INTEGER, city VARCHAR(255), timezone INTEGER, PRIMARY KEY (id))"
            #cursor.execute(cr_table_qr)
            print("aTable created successful")
    finally:
        connection.close()
except Exception as ex:
    print("Connection refused...")
    print(ex)

#            f"https://api.openweathermap.org/data/3.0/onecall?q={city}&exclude=current,minutely,daily&appid={open_weather_token}&units=metric"

def get_weather(lat, lon, open_weather_token):
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,daily,alerts&appid={open_weather_token}&units=metric")
            #f"https://api.openweathermap.org/data/2.5/find?q={city}&type=like&appid={open_weather_token}&units=metric"        )
        data = r.json();
        pprint(data)

        # ct = data['name']
        # weather_data = data["main"]["temp"]
        # speed_wind = data['wind']['speed']
        # print(f"City: {ct} \n temp: {weather_data} \n speed of wind: {speed_wind}")
    except Exception as ex:
        print(ex)
        print("Не корректное название города")

def main():
    # city_n = input()
    # get_weather(city_n, open_weather_token)
    numbers_input = input("Введите два нецелых числа через пробел: ")
    number1, number2 = map(float, numbers_input.split())
    get_weather(number1, number2, open_weather_token)

if __name__ == '__main__':
    main()


# import os
# from dotenv import load_dotenv
# import telebot
#
# # Load environment variables from .env file
# load_dotenv()
#
# API_KEY = os.getenv('API_KEY')
# bot = telebot.TeleBot(API_KEY)
#
# @bot.message_handler(commands=['Greet'])
# def greet(message):
#     bot.reply_to(message, "Sap! How ru?")
#
# bot.polling()


#
# @dp.message_handler()
# async def get_weather(message: types.Message):
#     try:
#         r = requests.get(
#             f"https://api.openweathermap.org/data/2.5/find?q={message.text}&type=like&appid={open_weather_token}&units=metric"
#         )
#         data = r.json()
#
#         if data["count"] > 1:
#             # Собираем список уникальных городов с их идентификаторами
#             cities_list = [f"{city['name']} ({city['sys']['country']}) [ID: {city['id']}]"
#                            for city in data['list']]
#             reply_message = "Найдено несколько городов:\n" + "\n".join(cities_list)
#             reply_message += "\nПожалуйста, отправьте ID города для получения погоды."
#             await message.reply(reply_message)
#         elif data["count"] == 1:
#             city = data['list'][0]
#             await send_weather_data(city, message)
#         else:
#             await message.reply("Город не найден. Проверьте название и попробуйте снова.")
#     except Exception as e:
#         await message.reply("Не удалось получить информацию о погоде.")
#         print(e)  # Для отладки
#
# @dp.message_handler(regexp=r"^\d+$")  # Упрощенное регулярное выражение для чисел
# async def get_weather_by_id(message: types.Message):
#     city_id = message.text.strip()  # Удаляем пробелы в начале и конце
#
#     try:
#         r = requests.get(
#             f"https://api.openweathermap.org/data/2.5/weather?id={city_id}&appid={open_weather_token}&units=metric"
#         )
#         if r.status_code == 200:
#             data = r.json()
#             await send_weather_data(data, message)
#         else:
#             # Логгируем детали ответа для диагностики
#             print(f"Error fetching weather data: Status Code {r.status_code}, Response {r.text}")
#             await message.reply("Город не найден. Проверьте ID и попробуйте снова.")
#     except Exception as e:
#         await message.reply("Не удалось получить информацию о погоде по ID города.")
#         print(f"Exception occurred: {e}")  # Для отладки
#
#
# # Функция отправки погоды пользователю
# async def send_weather_data(city, message):
#     city_name = city['name']
#     weather_data = city["main"]["temp"]
#     wind_speed = city['wind']['speed']
#
#     await message.reply(
#         f"Город: {city_name} \n Температура: {weather_data}°C \n Скорость ветра: {wind_speed} м/с"
#     )



#
# @dp.message_handler(state=WeatherForm.waiting_for_current_weather_city)
# async def current_weather_city_chosen(message: types.Message, state: FSMContext):
#     input_text = message.text.strip()
#
#     if ',' in input_text:
#         try:
#             lat, lon = map(float, input_text.split(','))
#             url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={open_weather_token}&units=metric"
#         except ValueError:
#             await message.reply(
#                 "Некорректный формат координат. Используйте формат 'широта,долгота'. Пожалуйста, попробуйте еще раз.")
#             # Не вызываем state.finish(), так как пользователь может попытаться ввести данные снова
#             return
#     else:
#         url = f"https://api.openweathermap.org/data/2.5/weather?q={input_text}&appid={open_weather_token}&units=metric"
#
#     try:
#         response = requests.get(url)
#
#         if response.status_code == 200:
#             data = response.json()
#             pprint(data)
#             weather_data = {
#                 "temp": data['main']['temp'],
#                 "cloudiness": data['clouds']['all'],
#                 "precipitation": data['rain']['1h'] if 'rain' in data else 'No rain',
#                 "pressure": data['main']['pressure'],
#                 "wind_speed": data['wind']['speed'],
#                 "wind_direction": data['wind']['deg'],
#                 "humidity": data['main']['humidity']
#             }
#
#             await message.reply(
#                 f"Погода в {data['name']}, {data['sys']['country']}:\n"
#                 f"Температура: {weather_data['temp']}°C\n"
#                 f"Облачность: {weather_data['cloudiness']}%\n"
#                 f"Осадки: {weather_data['precipitation']} mm/h\n"
#                 f"Давление: {weather_data['pressure']} hPa\n"
#                 f"Ветер: {weather_data['wind_speed']} м/с, направление {weather_data['wind_direction']}°\n"
#                 f"Влажность: {weather_data['humidity']}%\n"
#             )
#
#         else:
#             await message.reply("Не удалось получить данные о погоде. Проверьте ввод и попробуйте снова.")
#             # Здесь также можно дать пользователю возможность попробовать ввести данные еще раз, не вызывая state.finish()
#     except Exception as e:
#         logging.error(f"Ошибка при запросе к API погоды: {e}")
#         await message.reply("Произошла ошибка при запросе к API погоды.")
#




#
# @dp.message_handler(state=WeatherForm.waiting_for_current_weather_city)
# async def current_weather_city_chosen(message: types.Message, state: FSMContext):
#     city_name = message.text.strip()
#     url = f"http://api.openweathermap.org/data/2.5/find?q={city_name}&appid={open_weather_token}&type=like&units=metric"
#     response = requests.get(url)
#     data = response.json()
#
#     if response.status_code == 200 and data['count'] > 0:
#         if data['count'] == 1:
#             # Только один город найден
#             await send_weather_data(data['list'][0], message)
#             await state.finish()
#         else:
#             # Несколько городов найдено
#             cities = data['list']
#             keyboard = InlineKeyboardMarkup(row_width=2)  # Создаем клавиатуру
#
#             # Добавляем кнопку для каждого города
#             for city in cities:
#                 button_text = f"{city['name']}, {city['sys']['country']}"
#                 callback_data = f"city_{city['id']}"  # Используем уникальный идентификатор города в качестве callback_data
#                 keyboard.insert(InlineKeyboardButton(button_text, callback_data=callback_data))
#
#             await message.reply("Найдено несколько городов. Пожалуйста, выберите один:", reply_markup=keyboard)
#             # Устанавливаем состояние ожидания выбора города
#             await WeatherForm.waiting_for_city_selection.set()
#     else:
#         await message.reply("Город не найден. Пожалуйста, проверьте ввод и попробуйте снова.")

