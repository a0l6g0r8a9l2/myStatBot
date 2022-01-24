import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from handlers.utils import FillMetricValueStrategy
from services.metrics import Metric
from services.utils import create_file_path_if_not_exist
from utils import log_it, default_logger


class MetricsExporter(Metric):
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.file_name = 'metrics' + '_' + str(user_id) + '_' + \
                         datetime.datetime.now().strftime("%d-%m-%Y-%H-%M") + '.csv'

    @log_it(logger=default_logger)
    async def prepare_data_to_export(self, metrics: list[list], fill_empty_values: bool = True) -> pd.DataFrame:
        """
        Нормализовать имеющиеся данные и объединить их с пропущенными (если применимо)

        :param metrics: имеющиеся данные
        :param fill_empty_values: признак необходимости заполнения пропущенных данных
        """
        metrics_column_name = ['name', 'value', 'date', 'comment']
        filled_by_user_data = pd.DataFrame(metrics, columns=metrics_column_name)
        filled_by_user_data['date'] = pd.to_datetime(filled_by_user_data['date'], unit='ns').dt.date
        filled_by_user_data['value'] = pd.to_numeric(filled_by_user_data['value'], errors='coerce')
        filled_by_user_data['name'] = filled_by_user_data['name'].astype(str)
        filled_by_user_data = filled_by_user_data.replace({'comment': np.nan}, '-')

        if fill_empty_values:
            missing_data = await self.prepare_missing_data(filled_by_user_data)
            missing_df = pd.DataFrame(missing_data, columns=metrics_column_name)
            completed_data = filled_by_user_data.append(missing_df)
            return completed_data

        return filled_by_user_data

    @log_it(logger=default_logger)
    async def get_fill_value(self, metric_name: str, metric_values: pd.DataFrame) -> float:
        """
        Получить значение для заполнения пропущенных данных по выбранной метрике

        :param metric_name: выбранная метрика
        :param metric_values: имеющиеся данные
        """
        metric_info = await self.fetch_metrics_options()
        for m in metric_info:
            if m.get('name') == metric_name:
                if m.get('fill_strategy') == FillMetricValueStrategy.MEAN.name:
                    return round(float(metric_values.where(metric_values['name'] == metric_name).value.mean()), 2)
                elif m.get('fill_strategy') == FillMetricValueStrategy.MODE.name:
                    return round(float(metric_values.where(metric_values['name'] == metric_name).value.mode()[1]), 2)
                else:
                    return 0

    @log_it(logger=default_logger)
    async def prepare_missing_data(self, metric_values: pd.DataFrame) -> Optional[list[list]]:
        """
        Подготовить пропущенные данные

        :param metric_values: имеющиеся данные
        """
        # todo: заполнять пропущенные значения с дня первого значения КОНКРЕТНОЙ метрики (а не самой первой)
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
                value = await self.get_fill_value(name, metric_values)
                rows_to_add.append([name, value, date, '-'])
        return rows_to_add

    @log_it(logger=default_logger)
    async def export_data_to_csv(self, fill_empty_values: bool = True) -> Optional[Path]:
        """
        Экспортировать csv файл с данными для выгрузки

        :param fill_empty_values: признак необходимости заполнения пропущенных данных
        """
        data = await self.fetch_all()
        default_logger.debug(f'User metrics data: {data}')
        default_logger.debug(f'Should fill empty data: {fill_empty_values}')
        if not data:
            return None

        file_path = create_file_path_if_not_exist() / self.file_name
        export_data: pd.DataFrame = await self.prepare_data_to_export(data, fill_empty_values)
        export_data.to_csv(path_or_buf=file_path, index=False)
        return file_path
