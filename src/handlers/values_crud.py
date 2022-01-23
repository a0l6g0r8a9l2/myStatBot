import datetime

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.utils.emoji import emojize

from handlers.common import ConfirmOptions, MetricTypes
from services.exporter import MetricsExporter
from services.utils import remove_file
from src.store.services import fetch_all_metrics_names, fetch_user_metric_type, \
    fetch_values_user_metric, add_value_by_metric, fetch_all_metrics_hashtags, \
    delete_user_data
from utils import default_logger, log_it


class AddMetricValue(StatesGroup):
    waiting_for_metric_name = State()
    waiting_for_metric_value = State()
    waiting_for_metric_value_comment = State()


class DeleteValues(StatesGroup):
    waiting_for_confirm = State()


@log_it(logger=default_logger)
async def add_value(message: types.Message):
    """
    This handler will be called when user sends #some
    """
    if message.text.startswith('#'):
        try:
            user_input = message.text.lower()[1:]
            all_user_hashtags = await fetch_all_metrics_hashtags(message.from_user.id)
            if len(user_input.split()) >= 3:
                hashtag, value, comment = user_input.split(maxsplit=2)
            else:
                hashtag, value = user_input.split(maxsplit=1)
                comment = None
            metric_type = await fetch_user_metric_type(message.from_user.id, hashtag.replace('_', ' '))
            default_logger.debug(f'Metric type {metric_type} and message {value}')
            if (metric_type == MetricTypes.relative.value) and (int(value) > 5):
                await message.answer(f'Значение для метрики с типом <b>{metric_type}</b> должно быть от 1 до 5',
                                     parse_mode='HTML')
            elif all_user_hashtags and (hashtag in all_user_hashtags):
                await add_value_by_metric(value=value,
                                          hashtag=hashtag,
                                          name=hashtag.replace('_', ' '),
                                          user_id=message.from_user.id,
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
    await add_value_by_metric(value=metric_data.get('metric_value'),
                              hashtag=metric_data.get('metric_name').replace(" ", "_"),
                              name=metric_data.get('metric_name'),
                              user_id=message.from_user.id,
                              comment=metric_data.get('comment', '-'))
    await message.answer('👍')
    await state.finish()


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


@log_it(logger=default_logger)
async def confirm_delete_warning(message: types.Message):
    """
    This handler will be called first when user send `/delete` command
    """
    confirm_buttons = ConfirmOptions.list()
    actions_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    actions_keyboard.add(*[KeyboardButton(i) for i in confirm_buttons])
    await message.answer('<b>Внимание! Удаление данных необратимо!</b>\n\n'
                         'Перед удалением, рекомендуется выгрузить ваши данные командой <b>/export</b>\n\n'
                         '<b>Вы подтверждаете удаление?</b>',
                         reply_markup=actions_keyboard,
                         parse_mode='HTML')
    await DeleteValues.waiting_for_confirm.set()


@log_it(logger=default_logger)
async def delete_all(message: types.Message, state: FSMContext):
    """
    This handler will be called second when user send `/delete` command
    """
    if message.text == ConfirmOptions.TRUE.value:
        await delete_user_data(message.from_user.id)
        await message.answer(emojize('Ваши метрики удалены :heavy_exclamation_mark:'))
        await state.finish()
    else:
        await message.answer(emojize('Продолжаем вести статистику! :fire:'))
        await state.finish()
