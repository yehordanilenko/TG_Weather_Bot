import asyncio
from datetime import datetime, timedelta
import pytz
from weather import send_weather_forecast, get_coordinates_for_city
from database import get_user_timezone
import aiomysql
from config import db_config

async def scheduler(bot):
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
                        notification_time = user['notification_time']  # Received as timedelta

                        lat, lon = await get_coordinates_for_city(city)
                        if lat is None or lon is None:
                            print(f"Не удалось получить координаты для города: {city}")
                            continue

                        base_date = datetime(2000, 1, 1)  # Arbitrary base date
                        notification_time = (base_date + notification_time).time()

                        user_local_time = (utc_now + timedelta(hours=db_timezone)).time()

                        if user_local_time.strftime('%H:%M') == notification_time.strftime('%H:%M'):
                            await send_weather_forecast(bot, user_id, lat, lon, db_timezone)
                        else:
                            print(f"Not time yet for user {user_id}: {notification_time.strftime('%H:%M')} != {user_local_time.strftime('%H:%M')}")
        await asyncio.sleep(60)
