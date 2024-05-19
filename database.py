import aiomysql
from config import host, user, password, db_name

db_config = {
    'host': host,
    'port': 3306,
    'user': user,
    'password': password,
    'db': db_name,
    'cursorclass': aiomysql.DictCursor,
    'autocommit': True
}

async def add_or_update_user_in_db(user_id, city, timezone, notification_time):
    async with aiomysql.create_pool(**db_config) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
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
