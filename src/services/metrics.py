from typing import Optional

from src.store.mongo import MongodbService
from utils import log_it, default_logger


class Metric:
    """
    Базовый класс для работы с метриками
    """
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.metric_values_store = MongodbService(collection='user_metric_values')
        self.metric_options_store = MongodbService(collection='user_metrics')

    @log_it(logger=default_logger)
    async def fetch_all(self) -> Optional[list[list]]:
        """
        Получить все метрики
        """
        user_metrics_values = await self.metric_values_store.find(self.user_id)
        if user_metrics_values:
            return [[k.get('name'), k.get('value'), k.get('date'), k.get('comment', '-')] for k in
                    user_metrics_values]

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
