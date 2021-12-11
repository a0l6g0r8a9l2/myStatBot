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


async def add_value_by_metric(value: str, hashtag: str, user_id: str, comment: Optional[str] = None):
    db = MongodbService(collection='user_metric_values')
    await db.create_one(
        {'value': value,
         'hashtag': hashtag,
         'user_id': user_id,
         'date': datetime.datetime.today().isoformat(),
         'comment': comment}
    )


async def fetch_all_metrics(user_id: str):
    db = MongodbService(collection='user_metrics')
    user_metrics = await db.find(user_id)
    if user_metrics:
        return set(k.get('name') for k in user_metrics if user_metrics)
    else:
        return


async def fetch_all_metric_and_values(user_id: str):
    db = MongodbService(collection='user_metric_values')
    user_metrics_values = await db.find(user_id)
    if user_metrics_values:
        return [[k.get('hashtag'), k.get('value'), k.get('date'), k.get('comment', '-')] for k in user_metrics_values]
    else:
        return
