import datetime
from typing import Optional

from handlers.utils import FillMetricValueStrategy
from store.mongo import MongodbService
from utils import log_it, default_logger


class Metric:
    """
    Базовый класс для работы с метриками
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.metric_values_store = MongodbService(collection='user_metric_values')
        self.metric_options_store = MongodbService(collection='user_metrics')

    @staticmethod
    def hashtag_to_name(hashtag: str):
        return hashtag.replace('_', ' ')

    @log_it(logger=default_logger)
    async def fetch_all(self) -> Optional[list[list]]:
        """
        Получить все метрики
        """
        user_metrics_values = await self.metric_values_store.find(self.user_id)
        if user_metrics_values:
            return [[k.get('name') or self.hashtag_to_name(k.get('hashtag')), k.get('value'), k.get('date'), k.get('comment', '-')] for k in
                    user_metrics_values]

    @log_it(logger=default_logger)
    async def fetch_values_user_metric(self, metric_name: str) -> Optional[list[str]]:
        user_metrics_values = await self.metric_values_store.find(self.user_id)
        if user_metrics_values:
            return [k.get('value') for k in user_metrics_values if metric_name in (k.get('hashtag'), k.get('name'))]
        else:
            return

    @log_it(logger=default_logger)
    async def fetch_metrics_options(self) -> Optional[list[dict]]:
        """
        Получить параметры метрик
        """
        try:
            metrics_options = await self.metric_options_store.find(self.user_id)
            return metrics_options
        except (TypeError, ValueError) as err:
            default_logger.error(f'Ошибка поиска метрик! {err}')

    @log_it(logger=default_logger)
    async def update_option_by_metric_name(self, metric_name: str, metric_option: str, new_value: str) -> bool:
        """
        Обновить параметры метрики по названию (метрики)

        :param new_value: значение параметра для апдейта
        :param metric_option: параметр для апдейта
        :param metric_name: имя метрики
        """
        result = await self.metric_options_store.update_one_by_name(
            metric_name=metric_name,
            key=metric_option,
            value=new_value
                                                           )
        return result

    @log_it(logger=default_logger)
    async def add_metric(self, name: str, hashtag: str, metric_type: str,
                         fill_strategy: str = FillMetricValueStrategy.MEAN.value):
        await self.metric_options_store.create_one({'name': name,
                                                    'hashtag': hashtag,
                                                    'metric_type': metric_type,
                                                    'fill_strategy': fill_strategy,
                                                    'user_id': self.user_id})

    @log_it(logger=default_logger)
    async def add_value_by_metric(self, value: str, hashtag: str, name: str, comment: Optional[str] = None):
        await self.metric_values_store.create_one(
            {
                'value': value,
                'hashtag': hashtag,
                'name': name,
                'user_id': self.user_id,
                'date': datetime.datetime.today().isoformat(),
                'comment': comment
            }
        )

    @log_it(logger=default_logger)
    async def fetch_all_metrics_names(self):
        user_metrics = await self.fetch_metrics_options()
        if user_metrics:
            return set(k.get('name') for k in user_metrics if user_metrics)
        else:
            return

    @log_it(logger=default_logger)
    async def fetch_all_metrics_hashtags(self):
        user_metrics = await self.fetch_metrics_options()
        if user_metrics:
            return set(k.get('hashtag') for k in user_metrics if user_metrics)
        else:
            return

    @log_it(logger=default_logger)
    async def fetch_user_metric_types(self) -> Optional[list[dict]]:
        try:
            user_metrics = await self.fetch_metrics_options()
            metric_types = [{k.get('name'): k.get('metric_type')} for k in user_metrics]
            return metric_types
        except (TypeError, ValueError) as err:
            default_logger.error(f'Метрика без имени или типа! {err}')
            return None

    @log_it(logger=default_logger)
    async def fetch_user_metric_type(self, metric_name: str) -> Optional[str]:
        try:
            user_metrics_types = await self.fetch_user_metric_types()
            default_logger.debug(f'All metric types {user_metrics_types}')
            metric_type = [i.get(metric_name) for i in user_metrics_types if set(i.keys()).pop() == metric_name][0]
            return metric_type
        except (TypeError, ValueError, IndexError) as err:
            default_logger.error(f'Ошибка поиска типа метрики! {err}')
            return ''

    @log_it(logger=default_logger)
    async def delete_user_data(self):
        """ Removing data from all collection"""
        await self.metric_options_store.delete_many(value=self.user_id)
        await self.metric_values_store.delete_many(value=self.user_id)
