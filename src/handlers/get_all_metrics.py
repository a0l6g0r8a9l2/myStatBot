from aiogram import types

from services.metrics import Metric
from utils import log_it, default_logger


@log_it(logger=default_logger)
async def get_all_metrics(message: types.Message):
    """
    This handler will be called when user sends `/get_all_metrics` command
    """
    row_user_hashtags = await Metric(message.from_user.id).fetch_all_metrics_hashtags()
    if row_user_hashtags:
        prepared_hashtags = [f'#{i}' for i in row_user_hashtags]
        msg = '\n'.join(prepared_hashtags)
        await message.reply(msg)
    else:
        await message.answer('Не найдено ни одной метрики')
