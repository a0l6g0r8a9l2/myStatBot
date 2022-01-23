import datetime
from typing import Optional

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
async def fetch_values_user_metric(user_id: str, metric_name: str) -> Optional[list[str]]:
    db = MongodbService(collection='user_metric_values')
    user_metrics_values = await db.find(user_id)
    if user_metrics_values:
        return [k.get('value') for k in user_metrics_values if metric_name in (k.get('hashtag'), k.get('name'))]
    else:
        return


@log_it(logger=default_logger)
async def delete_user_data(user_id: str):
    """ Removing data from all collection"""
    values_collection = MongodbService(collection='user_metric_values')
    await values_collection.delete_many(value=user_id)
    metric_collection = MongodbService(collection='user_metrics')
    await metric_collection.delete_many(value=user_id)
