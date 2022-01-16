import csv
import datetime
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from handlers.common import FillMetricValueStrategy
from utils import log_it, default_logger
from .mongo import MongodbService


@log_it(logger=default_logger)
async def add_metric(name: str, hashtag: str, metric_type: str, user_id: str,
                     fill_strategy: str = FillMetricValueStrategy.MEAN.value):
    db = MongodbService(collection='user_metrics')
    await db.create_one({'name': name,
                         'hashtag': hashtag,
                         'metric_type': metric_type,
                         'fill_strategy': fill_strategy,
                         'user_id': user_id})


@log_it(logger=default_logger)
async def add_value_by_metric(value: str, hashtag: str, name: str, user_id: str, comment: Optional[str] = None):
    db = MongodbService(collection='user_metric_values')
    await db.create_one(
        {
            'value': value,
            'hashtag': hashtag,
            'name': name,
            'user_id': user_id,
            'date': datetime.datetime.today().isoformat(),
            'comment': comment
        }
    )


@log_it(logger=default_logger)
async def fetch_all_metrics_names(user_id: str):
    user_metrics = await fetch_user_metrics(user_id)
    if user_metrics:
        return set(k.get('name') for k in user_metrics if user_metrics)
    else:
        return


@log_it(logger=default_logger)
async def fetch_all_metrics_hashtags(user_id: str):
    user_metrics = await fetch_user_metrics(user_id)
    if user_metrics:
        return set(k.get('hashtag') for k in user_metrics if user_metrics)
    else:
        return


@log_it(logger=default_logger)
async def fetch_user_metric_type(user_id: str, metric_name: str) -> Optional[str]:
    try:
        user_metrics_types = await fetch_user_metric_types(user_id)
        default_logger.debug(f'All metric types {user_metrics_types}')
        metric_type = [i.get(metric_name) for i in user_metrics_types if set(i.keys()).pop() == metric_name][0]
        return metric_type
    except (TypeError, ValueError, IndexError) as err:
        default_logger.error(f'Ошибка поиска типа метрики! {err}')
        return ''


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
async def fill_empty_values(user_id: str, metrics: list[list]) -> pd.DataFrame:
    """
    Эта функция примет список значений, найдет пропуски значений по датам
    и заполнит их согласно стратегии заполнения пропущенных значений
    для данной метрики
    """
    metrics_column_name = ['name', 'value', 'comment', 'date']
    filled_by_user_data = pd.DataFrame(metrics, columns=metrics_column_name)
    filled_by_user_data['date'] = pd.to_datetime(filled_by_user_data['date'], unit='ns').dt.date
    filled_by_user_data['value'] = pd.to_numeric(filled_by_user_data['value'], errors='coerce')
    filled_by_user_data['name'] = filled_by_user_data['name'].astype(str)
    filled_by_user_data = filled_by_user_data.replace({'comment': np.nan}, '-')

    missing_data = prepare_missing_data(user_id, filled_by_user_data)
    missing_df = pd.DataFrame(missing_data, columns=metrics_column_name)

    completed_data = filled_by_user_data.append(missing_df)
    return completed_data


@log_it(logger=default_logger)
async def get_fill_value(user_id: str, metric_name: str, metric_values: pd.DataFrame) -> float:
    metric_info = await fetch_user_metrics(user_id)
    for m in metric_info:
        if m.get('name') == metric_name:
            if m.get('fill_strategy') == FillMetricValueStrategy.MEAN.value:
                return float(metric_values.where(metric_values['name'] == metric_name).value.mean())
            elif m.get('fill_strategy') == FillMetricValueStrategy.MODE.value:
                return float(metric_values.where(metric_values['name'] == metric_name).value.mode())
            else:
                return 0


@log_it(logger=default_logger)
def prepare_missing_data(user_id: str, metric_values: pd.DataFrame) -> Optional[list[list]]:
    min_date = metric_values['date'].min()
    max_date = metric_values['date'].max()
    observed_date = pd.date_range(min_date, max_date, freq='D')
    observed_date = pd.Series(observed_date, name='date')

    unique_metric_names = metric_values['name'].unique()

    rows_to_add = []
    for name in unique_metric_names:
        unique_date_with_metric = set(metric_values.where(metric_values['name'] == name)
                                      .dropna(subset=['name', 'value']).date.unique())
        date_range_set = set(observed_date.dt.date.unique())
        unique_date_without_metric = date_range_set - unique_date_with_metric
        for date in unique_date_without_metric:
            value = get_fill_value(user_id, name, metric_values)
            rows_to_add.append([name, value, '-', date])
    return rows_to_add


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
async def prepare_file_to_export(user_id: str) -> Optional[Path]:
    metric_values = await fetch_all_metric_and_values(user_id)
    if not metric_values:
        return None
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


@log_it(logger=default_logger)
async def delete_user_data(user_id: str):
    """ Removing data from all collection"""
    values_collection = MongodbService(collection='user_metric_values')
    await values_collection.delete_many(value=user_id)
    metric_collection = MongodbService(collection='user_metrics')
    await metric_collection.delete_many(value=user_id)
