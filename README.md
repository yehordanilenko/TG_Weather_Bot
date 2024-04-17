  Description

Created a Telegram bot. The main purpose is to send the user a weather forecast for the day for a selected city. Besides, it can send the current weather in the chosen city.

Working with the bot

The bot offers two functions: subscription to the weather forecast and current weather.

Subscription to the weather forecast

Users enter the name of the city or coordinates.
If the user enters a city and the bot finds several cities with that name, it will display all the variants with the country's abbreviation, so the user can select the desired city.
Users enter the time when they wish to receive the forecast.
Every day at the specified time, the bot sends the user a weather forecast at the indicated location starting from the following 8 hours.
The information about the weather includes temperature, humidity, and precipitation. If the user selects a precise location/time - the bot starts sending the data according to the new settings, i.e., a user can subscribe to only one place and time.
Current weather

The user enters the name of the city or coordinates.
If the user enters a city and the bot finds several cities with that name, it displays all the variants with the country's abbreviation, so the user can select the desired city.
The bot sends the current weather in the specified location.
The data about the weather includes temperature, humidity, precipitation, pressure, and wind intensity.
Features of the implementation

All necessary data the bot stores in MySQL.
