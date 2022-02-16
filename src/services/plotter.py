from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import seaborn as sns

from services.utils import create_file_path_if_not_exist
from services.exporter import MetricsExporter


async def get_user_data(user_id: str, fill_empty_values: bool = True) -> pd.DataFrame:
    exporter = MetricsExporter(user_id=user_id)
    data = await exporter.fetch_all_values()
    enriched_data = await exporter.prepare_data_to_export(metrics=data, fill_empty_values=fill_empty_values)
    return enriched_data


def prepare_data(data: pd.DataFrame) -> pd.DataFrame:
    data = data.drop(['type', 'comment', 'fill_strategy'], axis=1)
    # data = data.drop(data[data['value'].isnull() is True].index)

    result = data.pivot_table(index='date',
                              columns='name',  # значения станут колонками
                              values='value',  # к этим значениям будем применять аггрегацию
                              aggfunc='sum',  # функция агрегации
                              fill_value=np.nan)  # заменять выбранным значением
    return result


def prepare_plot(plot_data: pd.DataFrame, user_id: str, file_name: str = 'correlation_matrix.png') -> Optional[Path]:
    if plot_data.size <= 3:
        return None
    sns.set(rc={'figure.figsize': (15, 8)})  # size plot
    matrix = np.triu(plot_data.corr())  # prepare correlation matrix (triangle)
    fig = sns.heatmap(plot_data.corr(), annot=True, mask=matrix, fmt='.1g', vmin=-1, vmax=1, center=0, square=True)
    save_path = create_file_path_if_not_exist() / f'{user_id}_{datetime.now().strftime("%d-%m-%Y")}_{file_name}'
    fig.figure.savefig(save_path, format="png")
    return save_path
