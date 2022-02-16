import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InputFile, InlineKeyboardMarkup, InlineKeyboardButton

from handlers.utils import FillEmptyValuesOptions
from services.plotter import get_user_data, prepare_data, prepare_plot
from services.utils import remove_file
from utils import log_it, default_logger


class PlotStates(StatesGroup):
    waiting_for_fill_empty_values_confirm = State()


@log_it(logger=default_logger)
async def set_plot_options(message: types.Message):
    """
    This handler will be called first when user send `/correlation` command
    """
    actions_keyboard = InlineKeyboardMarkup(row_width=2)
    actions_keyboard.add(*[InlineKeyboardButton(i, callback_data=i) for i in FillEmptyValuesOptions.list()])
    await message.reply('Заполнить пропущенные значения?', reply_markup=actions_keyboard)
    await PlotStates.waiting_for_fill_empty_values_confirm.set()


@log_it(logger=default_logger)
async def export_plot(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called second when user send `/correlation` command
    """
    if callback_query.data == FillEmptyValuesOptions.RAW.value:
        fill_option = False
    else:
        fill_option = True
    row_user_data = await get_user_data(callback_query.from_user.id, fill_empty_values=fill_option)
    if row_user_data.empty:
        await callback_query.message.answer('Нет данных для построения графика')
        await state.finish()
    else:
        prepared_to_plot_data = prepare_data(data=row_user_data)
        plot_path = prepare_plot(plot_data=prepared_to_plot_data, user_id=callback_query.from_user.id)
        file = InputFile(plot_path, filename=f'Грфик корреляции {datetime.datetime.now().strftime("%d-%m-%Y %H-%M")}.png')
        await callback_query.message.answer_document(file)
        remove_file(plot_path)
        await state.finish()
