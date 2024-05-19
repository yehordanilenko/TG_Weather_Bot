from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
from config import tg_bot_token
from handlers import register_handlers
from scheduler import scheduler

async def main():
    bot = Bot(token=tg_bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    register_handlers(dp)  # Регистрируем обработчики без передачи бота

    asyncio.create_task(scheduler(bot))  # Передаем бота в планировщик
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
