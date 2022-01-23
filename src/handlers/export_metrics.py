import datetime

from aiogram import types
from aiogram.types import InputFile

from services.exporter import MetricsExporter
from services.utils import remove_file
from utils import log_it, default_logger


@log_it(logger=default_logger)
async def export(message: types.Message):
    """
    This handler will be called when user send `/export` command
    """
    file_path = await MetricsExporter(message.from_user.id).export_data_to_csv()
    if not file_path:
        await message.answer('Нет данных для выгрузки')
    else:
        file = InputFile(file_path, filename=f'Выгрузка по {datetime.datetime.now().strftime("%d-%m-%Y %H-%M")}.csv')
        await message.answer_document(file)
        remove_file(file_path)
