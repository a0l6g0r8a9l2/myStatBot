from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.emoji import emojize

from handlers.utils import ConfirmOptions
from store.services import delete_user_data
from utils import log_it, default_logger


class DeleteValues(StatesGroup):
    waiting_for_confirm = State()


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
