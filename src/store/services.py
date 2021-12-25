import csv
import datetime
import os
from pathlib import Path
from typing import Optional

from utils import log_it, default_logger
from .mongo import MongodbService


@log_it(logger=default_logger)
async def add_metric(name: str, hashtag: str, metric_type: str, user_id: str):
    db = MongodbService(collection='user_metrics')
    await db.create_one({'name': name,
                         'hashtag': hashtag,
                         'metric_type': metric_type,
                         'user_id': user_id})


@log_it(logger=default_logger)
async def add_value_by_metric(value: str, hashtag: str, name: str, user_id: str, comment: Optional[str] = None):
    db = MongodbService(collection='user_metric_values')
    await db.create_one(
        {'value': value,
         'hashtag': hashtag,
         'name': name,
         'user_id': user_id,
         'date': datetime.datetime.today().isoformat(),
         'comment': comment}
    )


@log_it(logger=default_logger)
async def fetch_all_metrics_names(user_id: str):
    user_metrics = await fetch_user_metrics(user_id)
    if user_metrics:
        return set(k.get('hashtag') for k in user_metrics if user_metrics)
    else:
        return


@log_it(logger=default_logger)
async def fetch_user_metric_type(user_id: str, metric_name: str) -> Optional[str]:
    try:
        user_metrics_types = await fetch_user_metric_types(user_id)
        metric_type = [i.get('metric_type') for i in user_metrics_types if i.get('name') == metric_name][0]
        return metric_type
    except (TypeError, ValueError) as err:
        default_logger.error(f'Ошибка поиска типа метрики! {err}')
        return None


@log_it(logger=default_logger)
async def fetch_user_metric_types(user_id: str) -> Optional[list[dict]]:
    try:
        user_metrics = await fetch_user_metrics(user_id)
        metric_types = [{k.get('name'): k.get('metric_type')} for k in user_metrics]
        return metric_types
    except (TypeError, ValueError) as err:
        default_logger.error(f'Метрика без имени или типа! {err}')
        return None


@log_it(logger=default_logger)
async def fetch_user_metrics(user_id: str) -> Optional[list[dict]]:
    try:
        db = MongodbService(collection='user_metrics')
        user_metrics = await db.find(user_id)
        return user_metrics
    except (TypeError, ValueError) as err:
        default_logger.error(f'Ошибка поиска метрик! {err}')
        return None


@log_it(logger=default_logger)
async def fetch_all_metric_and_values(user_id: str):
    db = MongodbService(collection='user_metric_values')
    user_metrics_values = await db.find(user_id)
    if user_metrics_values:
        return [[k.get('hashtag'), k.get('value'), k.get('date'), k.get('comment', '-')] for k in user_metrics_values]
    else:
        return


@log_it(logger=default_logger)
async def fetch_values_user_metric(user_id: str, metric_name: str) -> Optional[list[str]]:
    db = MongodbService(collection='user_metric_values')
    user_metrics_values = await db.find(user_id)
    if user_metrics_values:
        return [k.get('value') for k in user_metrics_values if metric_name in (k.get('hashtag'), k.get('name'))]
    else:
        return


@log_it(logger=default_logger)
def create_file_path_if_not_exist(path_from_current_dir: str = 'export') -> Path:
    path = Path.cwd() / path_from_current_dir
    if path.exists() is False:
        path.mkdir()
    return path


@log_it(logger=default_logger)
def create_csv_file(file_prefix_name: str, column_names: list, data: list[list], path: Optional[Path] = None) -> Path:
    if not path:
        path = create_file_path_if_not_exist()
    file_name = 'metrics' + '_' + str(file_prefix_name) + '_' + \
                datetime.datetime.now().strftime("%d-%m-%Y-%H-%M") + '.csv'
    path_to_file = path / file_name

    with open(path_to_file, 'w') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(column_names)
        csv_writer.writerows(data)

    return path_to_file


@log_it(logger=default_logger)
async def prepare_file_to_export(user_id: str) -> Path:
    metric_values = await fetch_all_metric_and_values(user_id)
    default_logger.debug(f'User metrics values: {metric_values}')
    metric_column_names = ['Метрика', 'Значение', 'Дата', 'Комментарий']
    file_path = create_csv_file(user_id, metric_column_names, metric_values)
    return file_path


@log_it(logger=default_logger)
def remove_file(path: Path):
    if path.is_file():
        os.remove(path)
        default_logger.debug('Файл удален')
    else:
        default_logger.warning('Файл не найден')