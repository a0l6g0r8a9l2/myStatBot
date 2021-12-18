import datetime
import logging
from typing import Optional

from src.config import settings
from .mongo import MongodbService

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.logging_level,
                    format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")


async def add_metric(name: str, hashtag: str, metric_type: str, user_id: str):
    db = MongodbService(collection='user_metrics')
    await db.create_one({'name': name,
                         'hashtag': hashtag,
                         'metric_type': metric_type,
                         'user_id': user_id})


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


async def fetch_all_metrics_names(user_id: str):
    db = MongodbService(collection='user_metrics')
    user_metrics = await db.find(user_id)
    if user_metrics:
        return set(k.get('name') for k in user_metrics if user_metrics)
    else:
        return


async def fetch_user_metric_type(user_id: str, metric_name: str) -> Optional[str]:
    try:
        db = MongodbService(collection='user_metrics')
        user_metrics = await db.find(user_id)
        metric_type = set(k.get('metric_type') for k in user_metrics
                          if metric_name in (k.get('name'), k.get('hashtag'))).pop()
        logging.debug(f'Log from {__name__} fetch_user_metric_type: {metric_type}')
        return metric_type
    except (TypeError, ValueError) as err:
        logger.error(f'Ошибка поиска типа метрики! {err}')
        return None


async def fetch_all_metric_and_values(user_id: str):
    db = MongodbService(collection='user_metric_values')
    user_metrics_values = await db.find(user_id)
    if user_metrics_values:
        return [[k.get('hashtag'), k.get('value'), k.get('date'), k.get('comment', '-')] for k in user_metrics_values]
    else:
        return


async def fetch_values_user_metric(user_id: str, metric_name: str) -> Optional[list[str]]:
    db = MongodbService(collection='user_metric_values')
    user_metrics_values = await db.find(user_id)
    if user_metrics_values:
        return [k.get('value') for k in user_metrics_values if metric_name in (k.get('hashtag'), k.get('name'))]
    else:
        return
