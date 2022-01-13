from enum import Enum

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.store.services import add_metric, fetch_all_metrics_names, fetch_all_metrics_hashtags
from utils import default_logger, log_it


@log_it(logger=default_logger)
async def get_all_metrics(message: types.Message):
    """
    This handler will be called when user sends `/get_all_metrics` command
    """
    row_user_hashtags = await fetch_all_metrics_hashtags(user_id=message.from_user.id)
    if row_user_hashtags:
        prepared_hashtags = [f'#{i}' for i in row_user_hashtags]
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
        await callback_query.message.answer('Такой тип не поддерживатеся.')
