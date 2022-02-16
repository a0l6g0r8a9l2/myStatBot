import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton

from handlers.utils import FillEmptyValuesOptions
from services.exporter import MetricsExporter
from services.utils import remove_file
from utils import log_it, default_logger


class ExportStates(StatesGroup):
    waiting_for_fill_empty_values_confirm = State()


@log_it(logger=default_logger)
async def set_export_options(message: types.Message):
    """
    This handler will be called first when user send `/export` command
    """
    actions_keyboard = InlineKeyboardMarkup(row_width=2)
    actions_keyboard.add(*[InlineKeyboardButton(i, callback_data=i) for i in FillEmptyValuesOptions.list()])
    await message.reply('Заполнить пропущенные значения?', reply_markup=actions_keyboard)
    await ExportStates.waiting_for_fill_empty_values_confirm.set()


@log_it(logger=default_logger)
async def export(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called second when user send `/export` command
    """
    if callback_query.data == FillEmptyValuesOptions.RAW.value:
        fill_option = False
    else:
        fill_option = True
    file_path = await MetricsExporter(callback_query.from_user.id).export_data_to_csv(fill_option)
    if not file_path:
        await callback_query.message.answer('Нет данных для выгрузки')
    else:
        file = InputFile(file_path, filename=f'Выгрузка по {datetime.datetime.now().strftime("%d-%m-%Y %H-%M")}.csv')
        await callback_query.message.answer_document(file)
        remove_file(file_path)
        await state.finish()
