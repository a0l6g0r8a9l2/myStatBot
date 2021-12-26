import datetime
from enum import Enum

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InputFile

from src.store.services import add_metric, fetch_all_metrics_names, add_value_by_metric, fetch_all_metric_and_values, \
    prepare_file_to_export, remove_file, fetch_all_metrics_hashtags
from utils import default_logger, log_it


async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Привет, это бот для сбора статистики!")


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
            if all_user_hashtags and (hashtag in all_user_hashtags):
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
async def get_all_metric_values(message: types.Message):
    """
    This handler will be called when user sends `/get_all_metric_values` command
    """
    metrics_values = await fetch_all_metric_and_values(message.from_user.id)
    if metrics_values:
        msg = 'Метрика, Значение, Дата, Комментарий' + '\n'
        for row in metrics_values:
            for i, value in enumerate(row):
                default_logger.debug(f'Номер значения {i}, значение {value}')
                if not value:
                    value = '-'
                elif i == 2:
                    value = datetime.datetime.fromisoformat(value).strftime("%d.%m.%Y %H:%M")
                msg += value + ', '
            msg += '\n'
        await message.reply(msg)
    else:
        await message.reply('Не найдено ни однного значения метрик')


@log_it(logger=default_logger)
async def export(message: types.Message):
    """
    This handler will be called when user send `/export` comand
    :param message:
    :return:
    """
    file_path = await prepare_file_to_export(message.from_user.id)
    file = InputFile(file_path, filename=f'Выгрузка по {datetime.datetime.now().strftime("%d-%m-%Y %H-%M")}')
    await message.answer_document(file)
    remove_file(file_path)


@log_it(logger=default_logger)
async def get_all_metrics(message: types.Message):
    """
    This handler will be called when user sends `/get_all_metrics` command
    """
    row_user_hashtags = await fetch_all_metrics_hashtags(user_id=message.from_user.id)
    prepared_hashtags = [f'#{i}' for i in row_user_hashtags if row_user_hashtags]
    if len(prepared_hashtags) > 0:
        msg = '\n'.join(prepared_hashtags)
        await message.reply(msg)
    else:
        await message.answer('Не найдено ни одной метрики')


class MetricTypes(Enum):
    absolute = 'количественная'
    relative = 'качественная'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, MetricTypes))


class AddMetric(StatesGroup):
    waiting_for_name = State()
    waiting_for_type = State()


@log_it(logger=default_logger)
async def new_metric(message: types.Message):
    """
    This handler will be called when user sends `/new_metric` command
    """
    await message.reply("Ок, новая метрикка. Давай добавим ей название")
    await AddMetric.waiting_for_name.set()


@log_it(logger=default_logger)
async def waiting_for_metric_name(message: types.Message, state: FSMContext):
    """
    This handler will be called when user sends `/new_metric` command
    """
    await state.update_data(metric_name=message.text.lower(), user_id=message.from_user.id)
    actions_keyboard = InlineKeyboardMarkup(row_width=3)
    actions_keyboard.row(*[InlineKeyboardButton(i, callback_data=i) for i in MetricTypes.list()])
    user_metrics = await fetch_all_metrics_names(message.from_user.id)
    if (user_metrics is None) or (message.text.lower() not in user_metrics):
        await message.answer(f"Ok, метрика <u>{message.text.lower()}</u>. Давай выберем тип:",
                             reply_markup=actions_keyboard, parse_mode="HTML")
        await AddMetric.waiting_for_type.set()
    else:
        await message.answer(f'Метрика <b>{message.text.lower()}</b> уже существует!', parse_mode='HTML')
        await state.finish()


@log_it(logger=default_logger)
async def waiting_for_metric_type(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called when user sends `/new_metric` command
    """
    if callback_query.data in MetricTypes.list():
        await state.update_data(metric_type=callback_query.data)
        metric = await state.get_data()
        await add_metric(
            name=metric.get('metric_name'),
            hashtag=str(metric.get('metric_name')).replace(' ', '_'),
            metric_type=metric.get('metric_type'),
            user_id=metric.get('user_id')
        )
        await callback_query.message.answer(f'👍\n'
                                            f'Теперь можешь добалять значение метрики по '
                                            f'#{str(metric.get("metric_name")).replace(" ", "_")} значение комментарий')
        await state.finish()
    else:
        await callback_query.message.answer(f'Такой тип не поддерживатеся.')
