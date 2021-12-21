import logging
from functools import wraps

from aiogram import types

from config import settings


def get_logger() -> logging.Logger:
    """
    Default logger
    :return: logging.Logger
    """
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=settings.logging_level,
                        format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s -"
                               " %(lineno)d - %(message)s")

    return logger


default_logger = get_logger()


def log_it(logger: logging.Logger = default_logger):
    def log_it_outer(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            for arg in args:
                if isinstance(arg, types.Message):
                    logger.debug(f'Getting message: {arg.text} in function {function.__name__}', )
                if isinstance(arg, types.CallbackQuery):
                    logger.debug(f'Getting callback message: {arg.data} in function {function.__name__}', )
                else:
                    logger.debug(f'Getting func call with args: {arg} in function {function.__name__}')
            for key, value in kwargs.items():
                if isinstance(value, types.Message):
                    logger.debug(f'Getting message: key={key}, value={value.text} in function {function.__name__}', )
                if isinstance(value, types.CallbackQuery):
                    logger.debug(
                        f'Getting callback message: key={key}, value={value.data} in function {function.__name__}', )
                else:
                    logger.debug(f'Calling function {function.__name__} with key={key}, value={value}')

            logging.info(f'Exiting function {function.__name__}', )
            return function(*args, **kwargs)

        return wrapper

    return log_it_outer
