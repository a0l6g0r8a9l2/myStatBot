import os
from pathlib import Path

from utils import log_it, default_logger


@log_it(logger=default_logger)
def create_file_path_if_not_exist(path_from_current_dir: str = 'export') -> Path:
    """
    Проверяем есть ли директория, если нет - создаем

    :param path_from_current_dir: относительный путь
    """
    path = Path.cwd() / path_from_current_dir
    if path.exists() is False:
        path.mkdir()
    return path


@log_it(logger=default_logger)
def remove_file(path: Path):
    """
    Удаляем файл

    :param path: путь до файла
    """
    if path.is_file():
        os.remove(path)
        default_logger.debug('Файл удален')
    else:
        default_logger.warning('Файл не найден')
