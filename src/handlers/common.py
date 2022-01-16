from enum import Enum

from aiogram import types


class ConfirmOptions(Enum):
    TRUE = 'Подтверждаю'
    FALSE = 'Отмена'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, ConfirmOptions))


class FillMetricValueStrategy(Enum):
    ZERO = 'ноль'
    MEAN = 'среднее значение'
    MODE = 'модальное значение (самое частое)'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, FillMetricValueStrategy))


async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Привет, это бот для сбора статистики!")


class MetricTypes(Enum):
    absolute = 'количественная'
    relative = 'качественная'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, MetricTypes))
