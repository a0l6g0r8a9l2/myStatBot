from enum import Enum

from aiogram import types


class ConfirmOptions(Enum):
    true = 'Подтверждаю'
    false = 'Отмена'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, ConfirmOptions))


async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Привет, это бот для сбора статистики!")
