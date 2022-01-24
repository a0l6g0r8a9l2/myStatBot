from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.utils import FillMetricValueStrategy, MetricTypes
from services.metrics import Metric
from utils import default_logger, log_it


class AddMetric(StatesGroup):
    waiting_for_name = State()
    waiting_for_type = State()
    waiting_for_fill_strategy = State()


@log_it(logger=default_logger)
async def new_metric(message: types.Message):
    """
    This handler will be called first when user sends `/new_metric` command
    """
    await message.reply("Ок, новая метрикка. Давай добавим ей название")
    await AddMetric.waiting_for_name.set()


@log_it(logger=default_logger)
async def waiting_for_metric_name(message: types.Message, state: FSMContext):
    """
    This handler will be called second when user sends `/new_metric` command
    """
    await state.update_data(metric_name=message.text.lower(), user_id=message.from_user.id)
    actions_keyboard = InlineKeyboardMarkup(row_width=3)
    actions_keyboard.row(*[InlineKeyboardButton(i, callback_data=i) for i in MetricTypes.list()])
    user_metrics = await Metric(message.from_user.id).fetch_all_metrics_names()
    if (user_metrics is None) or (message.text.lower() not in user_metrics):
        await message.answer(f"Ok, метрика <u>{message.text.lower()}</u>. Давай выберем тип:",
                             reply_markup=actions_keyboard, parse_mode='HTML')
        await AddMetric.waiting_for_type.set()
    else:
        await message.answer(f'Метрика <b>{message.text.lower()}</b> уже существует!', parse_mode='HTML')
        await state.finish()


@log_it(logger=default_logger)
async def waiting_for_metric_type(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called third when user sends `/new_metric` command
    """
    if callback_query.data in MetricTypes.list():
        await state.update_data(metric_type=callback_query.data)
        await callback_query.message.answer(f'<b>Ок, тип метрики - {callback_query.data}</b>.\n'
                                            'Осталось выбрать вариант заполнения пропущенных значений. '
                                            'Это упростит внесение и улучишит качество собираемой статистики!',
                                            parse_mode='HTML')
        actions_keyboard = InlineKeyboardMarkup(row_width=2)
        actions_keyboard.row(*[InlineKeyboardButton(i, callback_data=i) for i in FillMetricValueStrategy.list()])
        await callback_query.message.answer('Для заполнения пропущенных данных нужно использовать:',
                                            reply_markup=actions_keyboard)
        await AddMetric.waiting_for_fill_strategy.set()
    else:
        await callback_query.message.answer('Такой тип не поддерживатеся.')


@log_it(logger=default_logger)
async def waiting_for_fill_empty_values_strategy(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called fourth when user sends `/new_metric` command
    """
    if callback_query.data in FillMetricValueStrategy.list():
        metric_state_store = await state.get_data()
        name = metric_state_store.get('metric_name')
        kind = metric_state_store.get('metric_type')
        fill_strategy = FillMetricValueStrategy(callback_query.data).name
        await Metric(callback_query.from_user.id).add_metric(
            name=name,
            hashtag=str(name).replace(' ', '_'),
            metric_type=kind,
            fill_strategy=fill_strategy
        )
        await callback_query.message.answer(f'👍\n'
                                            f'Теперь можешь добалять значение метрики по '
                                            f'#{str(metric_state_store.get("metric_name")).replace(" ", "_")} '
                                            f'значение комментарий')
        await state.finish()
    else:
        await callback_query.message.answer('Такой вариант не поддерживатеся.')
