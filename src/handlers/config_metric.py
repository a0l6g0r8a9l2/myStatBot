from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.utils import FillMetricValueStrategy
from services.metrics import Metric
from utils import log_it, default_logger


class ConfigMetric(StatesGroup):
    waiting_for_metric_name = State()
    waiting_for_fill_strategy = State()


@log_it(logger=default_logger)
async def metric_to_config(message: types.Message):
    """
    This handler will be called first when user sends `/config_metrics` command
    """
    user_metrics = await Metric(message.from_user.id).fetch_all_metrics_names()
    if user_metrics:
        actions_keyboard = InlineKeyboardMarkup(row_width=3)
        actions_keyboard.add(*[InlineKeyboardButton(i, callback_data=i) for i in user_metrics])
        await message.reply("Ок, какую метрику настроим?", reply_markup=actions_keyboard)
        await ConfigMetric.waiting_for_metric_name.set()
    else:
        await message.reply('Не найдено ни одной метрики.\n'
                            'Создайте первую с помощью команды /new_metric')


@log_it(logger=default_logger)
async def waiting_for_strategy_name(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called second when user sends `/config_metrics` command
    """
    user_metrics = await Metric(callback_query.from_user.id).fetch_all_metrics_names()
    if callback_query.data in user_metrics:
        await state.update_data(metric_name=callback_query.data)
        actions_keyboard = InlineKeyboardMarkup(row_width=2)
        actions_keyboard.row(*[InlineKeyboardButton(i, callback_data=i) for i in FillMetricValueStrategy.list()])
        await callback_query.message.answer(f'Ok, метрика <b>{callback_query.data}</b>.\n'
                                            f'Какой вариант заполнения пропущенных значений выберем?',
                                            reply_markup=actions_keyboard, parse_mode='HTML')
        await ConfigMetric.waiting_for_fill_strategy.set()
    else:
        await callback_query.message.answer('Не нашел метрику.')


@log_it(logger=default_logger)
async def waiting_for_fill_strategy(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called second when user sends `/config_metrics` command
    """
    if callback_query.data in FillMetricValueStrategy.list():
        fill_strategy = FillMetricValueStrategy(callback_query.data).name
        await state.update_data(fill_strategy=fill_strategy)
        metric_state_store = await state.get_data()
        metric_name = metric_state_store.get('metric_name')
        result = await Metric(callback_query.from_user.id).update_option_by_metric_name(
            metric_name=metric_name,
            metric_option='fill_strategy',
            new_value=fill_strategy
        )
        if result:
            await callback_query.message.answer(f'👍')
        else:
            await callback_query.message.answer(f'Что-то пошло не так..')
        await state.finish()
    else:
        await callback_query.message.answer('Такой тип не поддерживатеся.')
