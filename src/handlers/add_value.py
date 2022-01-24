from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from handlers.utils import MetricTypes
from services.metrics import Metric
from utils import default_logger, log_it


class AddMetricValue(StatesGroup):
    waiting_for_metric_name = State()
    waiting_for_metric_value = State()
    waiting_for_metric_value_comment = State()


@log_it(logger=default_logger)
async def add_value(message: types.Message):
    """
    This handler will be called when user sends #some
    """
    if message.text.startswith('#'):
        try:
            user_input = message.text.lower()[1:]
            all_user_hashtags = await Metric(message.from_user.id).fetch_all_metrics_hashtags()
            if len(user_input.split()) >= 3:
                hashtag, value, comment = user_input.split(maxsplit=2)
            else:
                hashtag, value = user_input.split(maxsplit=1)
                comment = None
            metric_type = await Metric(message.from_user.id).fetch_user_metric_type(hashtag.replace('_', ' '))
            default_logger.debug(f'Metric type {metric_type} and message {value}')
            if (metric_type == MetricTypes.relative.value) and (int(value) > 5):
                await message.answer(f'Значение для метрики с типом <b>{metric_type}</b> должно быть от 1 до 5',
                                     parse_mode='HTML')
            elif all_user_hashtags and (hashtag in all_user_hashtags):
                await Metric(message.from_user.id).add_value_by_metric(value=value,
                                                                       hashtag=hashtag,
                                                                       name=hashtag.replace('_', ' '),
                                                                       comment=comment)
                await message.reply('👍')
            else:
                await message.reply('Не нашел метрику')
        except ValueError:
            await message.reply(f'Забыл ввести значение после {message.text}?')
    else:
        await message.reply('Не понял что нужно сделать')


@log_it(logger=default_logger)
async def new_value_to_metric(message: types.Message):
    """
    This handler will be called when user sends `/add_value` command
    """
    user_metrics = await Metric(message.from_user.id).fetch_all_metrics_names()
    if user_metrics:
        actions_keyboard = InlineKeyboardMarkup(row_width=3)
        actions_keyboard.add(*[InlineKeyboardButton(i, callback_data=i) for i in user_metrics])
        await message.reply("Ок, новое значение. Выбери метрику:", reply_markup=actions_keyboard)
        await AddMetricValue.waiting_for_metric_name.set()
    else:
        await message.reply('Не найдено ни одной метрики.\n'
                            'Создайте первую с помощью команды /new_metric')


@log_it(logger=default_logger)
async def waiting_for_name_of_metric(callback_query: types.CallbackQuery, state: FSMContext):
    user_metrics = await Metric(callback_query.from_user.id).fetch_all_metrics_names()
    if callback_query.data in user_metrics:
        await state.update_data(metric_name=callback_query.data)
        user_metric = Metric(callback_query.from_user.id)
        metric_type = await user_metric.fetch_user_metric_type(callback_query.data)
        user_metrics_values = await user_metric.fetch_values_user_metric(callback_query.data)
        if metric_type == MetricTypes.relative.value:
            unique_metrics_values = list(map(str, range(1, 6)))
        else:
            if isinstance(user_metrics_values, list):
                unique_metrics_values = set(user_metrics_values)
            else:
                unique_metrics_values = []
        await state.update_data(metric_type=metric_type)
        actions_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        actions_keyboard.add(*[KeyboardButton(i) for i in unique_metrics_values])
        await callback_query.message.answer(f'Метрика {metric_type}, выберите значение или напишите свое:',
                                            reply_markup=actions_keyboard)
        await AddMetricValue.waiting_for_metric_value.set()
    else:
        await callback_query.message.reply('<b>Такой метрики не найдено!</b>\n'
                                           'Выберите из списка метрик (/get_all_metrics) или\n '
                                           'создайте новую (/new_metric)', parse_mode='HTML')
        await state.finish()


@log_it(logger=default_logger)
async def waiting_for_metric_value(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        state_data = await state.get_data()
        metric_type = state_data.get('metric_type')
        if (metric_type == MetricTypes.relative.value) and (int(message.text) > 5):
            await message.answer(f'Значение для метрики с типом <b>{metric_type}</b> должно быть от 1 до 5',
                                 parse_mode='HTML')
        else:
            actions_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            actions_keyboard.add(KeyboardButton('Закончить'))
            await state.update_data(metric_value=message.text)
            await message.answer(f'Ок, значение <b>{message.text}</b>.\n'
                                 f'Добавь комментарий или нажми <b>"Закончить"</b>',
                                 reply_markup=actions_keyboard,
                                 parse_mode='HTML')
            await AddMetricValue.waiting_for_metric_value_comment.set()
    else:
        msg = '<b>Значение должно быть числовым!</b>\n'
        msg += f'- от <b>1 до 5</b>, если метрика {MetricTypes.relative.value}\n'
        msg += f'- <b>неотрицательное число</b>, если метрика {MetricTypes.absolute.value}'
        await message.answer(msg, parse_mode='HTML')


@log_it(logger=default_logger)
async def waiting_for_metric_value_comment(message: types.Message, state: FSMContext):
    if message.text != 'Закончить':
        await state.update_data(comment=message.text)
    metric_data = await state.get_data()
    await Metric(message.from_user.id).add_value_by_metric(value=metric_data.get('metric_value'),
                                                           hashtag=metric_data.get('metric_name').replace(" ", "_"),
                                                           name=metric_data.get('metric_name'),
                                                           comment=metric_data.get('comment', '-'))
    await message.answer('👍')
    await state.finish()
