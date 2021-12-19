import logging
import datetime

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from enum import Enum

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.store.services import add_metric, fetch_all_metrics_names, add_value_by_metric, fetch_all_metric_and_values
from src.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.logging_level,
                    format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")


async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Привет, это бот для сбора статистики!")


async def add_value(message: types.Message):
    """
    This handler will be called when user sends #some
    """
    logging.debug(f'Log from {__name__}: {message.text}')
    if message.text.startswith('#'):
        try:
            _message = message.text.lower()[1:]
            user_metrics = await fetch_all_metrics_names(message.from_user.id)
            if len(_message.split()) >= 3:
                name, value, comment = _message.split()
            else:
                name, value = _message.split()
                comment = None
            if user_metrics and (name in user_metrics):
                await add_value_by_metric(value=value, hashtag=name, name=name, user_id=message.from_user.id, comment=comment)
                await message.reply('👍')
            else:
                await message.reply('Не нашел метрику')
        except ValueError:
            await message.reply(f'Забыл ввести значение после {message.text}?')
    else:
        await message.reply('Не понял что нужно сделать')


async def get_all_metric_values(message: types.Message):
    """
    This handler will be called when user sends `/get_all_metric_values` command
    """
    logging.debug(f'Log from {__name__}: {message.text}')
    metrics_values = await fetch_all_metric_and_values(message.from_user.id)
    if metrics_values:
        msg = 'Метрика, Значение, Дата, Комментарий' + '\n'
        for row in metrics_values:
            for i, value in enumerate(row):
                logger.debug(f'Номер значения {i}, значение {value}')
                if not value:
                    value = '-'
                elif i == 2:
                    value = datetime.datetime.fromisoformat(value).strftime("%d.%m.%Y %H:%M")
                msg += value + ', '
            msg += '\n'
        await message.reply(msg)
    else:
        await message.reply('Не найдено ни однного значения метрик')


async def get_all_metrics(message: types.Message):
    """
    This handler will be called when user sends `/get_all_metrics` command
    """
    logging.debug(f'Log from {__name__}: {message.text}')
    metrics = await fetch_all_metrics_names(user_id=message.from_user.id)
    if metrics:
        msg = ''
        for metric in metrics:
            msg += '#' + metric + '\n'
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


async def new_metric(message: types.Message):
    """
    This handler will be called when user sends `/new_metric` command
    """
    logging.debug(f'Log from {__name__}: {message.text}')
    await message.reply("Ок, новая метрикка. Давай добавим ей название")
    await AddMetric.waiting_for_name.set()


async def waiting_for_metric_name(message: types.Message, state: FSMContext):
    """
    This handler will be called when user sends `/new_metric` command
    """
    logging.debug(f'Log from {__name__}: {message.text}')
    await state.update_data(metric_name=message.text.lower(), user_id=message.from_user.id)
    actions_keyboard = InlineKeyboardMarkup(row_width=3)
    actions_keyboard.row(*[InlineKeyboardButton(i, callback_data=i) for i in MetricTypes.list()])
    user_metrics = await fetch_all_metrics_names(message.from_user.id)
    if (user_metrics is None) or (message.text.lower() not in user_metrics):
        await message.answer(f"Ok, метрика <u>{message.text.lower()}</u>. Давай выберем тип:",
                             reply_markup=actions_keyboard, parse_mode="HTML")
        await AddMetric.waiting_for_type.set()
    else:
        await message.answer(f'Метрика {message.text.lower()} уже существует!')
        await state.finish()


async def waiting_for_metric_type(callback_query: types.CallbackQuery, state: FSMContext):
    """
    This handler will be called when user sends `/new_metric` command
    """
    logging.debug(f'Log from {__name__}: {callback_query.data}')
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


def register_metric_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start', 'help'], state='*')
    dp.register_message_handler(add_value, regexp='^#(\w+|\d)', state='*')
    dp.register_message_handler(get_all_metric_values, commands=['get_metrics_and_values'], state='*')
    dp.register_message_handler(get_all_metrics, commands=['get_metrics'], state='*')
    dp.register_message_handler(new_metric, commands=['new_metric'], state='*')
    dp.register_message_handler(waiting_for_metric_name, state=AddMetric.waiting_for_name, regexp='^[\w+]\w+')
    dp.register_callback_query_handler(waiting_for_metric_type, state=AddMetric.waiting_for_type)
