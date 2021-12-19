import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import BotCommand
from aiogram.utils.exceptions import TelegramAPIError

from handlers import register_handlers
from config import settings
from src.utils.middlewares import AccessMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.logging_level,
                    format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")


async def set_commands(tg_bot: Bot):
    commands = [
        BotCommand(command="/new_metric", description="Добавить метрику"),
        BotCommand(command="/add_value", description="Добавить значение метрике"),
        BotCommand(command="/get_metrics", description="Получить все метрики"),
        BotCommand(command="/get_metrics_and_values", description="Получить все метрики и значения")
    ]
    await tg_bot.set_my_commands(commands)


API_TOKEN = settings.telegram_token


async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(bot, storage=MemoryStorage())
    dp.middleware.setup(LoggingMiddleware())
    dp.middleware.setup(AccessMiddleware(settings.telegram_chat_id))
    register_handlers(dp)
    await set_commands(bot)
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info(f'Buy!')
    except TelegramAPIError as err:
        logging.error(f'Handling error: {err.args}')
