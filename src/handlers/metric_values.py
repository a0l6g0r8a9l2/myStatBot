from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from handlers.metrics import MetricTypes
from src.store.services import fetch_all_metrics_names, fetch_user_metric_type, \
    fetch_values_user_metric, add_value_by_metric
from utils import default_logger, log_it


class AddMetricValue(StatesGroup):
    waiting_for_metric_name = State()
    waiting_for_metric_value = State()
    waiting_for_metric_value_comment = State()


@log_it(logger=default_logger)
async def new_value_to_metric(message: types.Message):
    """
    This handler will be called when user sends `/add_value` command
    """
    user_metrics = await fetch_all_metrics_names(user_id=message.from_user.id)
    actions_keyboard = InlineKeyboardMarkup(row_width=3)
    actions_keyboard.add(*[InlineKeyboardButton(i, callback_data=i) for i in user_metrics])
    await message.reply("Ок, новое значение. Выбери метрику:", reply_markup=actions_keyboard)
    await AddMetricValue.waiting_for_metric_name.set()


@log_it(logger=default_logger)
async def waiting_for_name_of_metric(callback_query: types.CallbackQuery, state: FSMContext):
    user_metrics = await fetch_all_metrics_names(user_id=callback_query.from_user.id)
    if callback_query.data in user_metrics:
        await state.update_data(metric_name=callback_query.data)
        metric_type = await fetch_user_metric_type(callback_query.from_user.id, callback_query.data)
        user_metrics_values = await fetch_values_user_metric(callback_query.from_user.id, callback_query.data)
        if metric_type == MetricTypes.relative.value:
            unique_metrics_values = list(map(str, range(1, 6)))
        else:
            if isinstance(user_metrics_values, list):
                unique_metrics_values = set(user_metrics_values)
            else:
                unique_metrics_values = []
        actions_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        actions_keyboard.add(*[KeyboardButton(i) for i in unique_metrics_values])
        await callback_query.message.answer(f'Метрика {metric_type}, выберите значение или напишите свое:',
                                            reply_markup=actions_keyboard)
        await AddMetricValue.waiting_for_metric_value.set()
    else:
        await callback_query.message.reply('Такой метрики не найдено!\n'
                                           'Выберите из списка метрик (/get_all_metrics) или\n '
                                           'создайте новую (/new_metric)')
        await state.finish()


@log_it(logger=default_logger)
async def waiting_for_metric_value(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        actions_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        actions_keyboard.add(KeyboardButton('Закончить'))
        await state.update_data(metric_value=message.text)
        await message.answer(f'Ок, значение {message.text}.\n'
                             f'Добавь комментарий или нажми "Закончить"', reply_markup=actions_keyboard)
        await AddMetricValue.waiting_for_metric_value_comment.set()
    else:
        msg = f'<b>Значение должно быть числовым!</b>\n'
        msg += f'- от <b>1 до 5</b>, если метрика {MetricTypes.relative.value}\n'
        msg += f'- <b>неотрицательное число</b>, если метрика {MetricTypes.absolute.value}'
        await message.answer(msg, parse_mode='HTML')


@log_it(logger=default_logger)
async def waiting_for_metric_value_comment(message: types.Message, state: FSMContext):
    metric_data = await state.get_data()
    if message.text != 'Закончить':
        await state.update_data(comment=message.text)
    await add_value_by_metric(value=metric_data.get('metric_value'),
                              hashtag=metric_data.get('metric_name'),
                              name=metric_data.get('metric_name'),
                              user_id=message.from_user.id,
                              comment=metric_data.get('comment', '-'))
    await message.answer(f'👍')
    await state.finish()

