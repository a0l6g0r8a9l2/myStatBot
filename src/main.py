import asyncio

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import BotCommand
from aiogram.utils.exceptions import TelegramAPIError

from config import settings
from handlers import register_handlers
from src.utils.middlewares import AccessMiddleware
from utils import default_logger


async def set_commands(tg_bot: Bot):
    commands = [
        BotCommand(command="/new_metric", description="Добавить метрику"),
        BotCommand(command="/add_value", description="Добавить значение метрике"),
        BotCommand(command="/get_metrics", description="Получить все метрики"),
        BotCommand(command="/export", description="Экспорт в .csv"),
        BotCommand(command="/delete_all", description="Удалить все сохраненные метрики"),
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
        default_logger.info('Buy!')
    except TelegramAPIError as err:
        default_logger.error(f'Handling error: {err.args}')
