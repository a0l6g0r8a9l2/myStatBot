from aiogram import Dispatcher

from handlers.add_value import new_value_to_metric, waiting_for_name_of_metric, AddMetricValue, \
    waiting_for_metric_value_comment, waiting_for_metric_value, add_value
from handlers.delete_metrics import DeleteValues, confirm_delete_warning, delete_all
from handlers.export_metrics import export, set_export_options, ExportStates
from handlers.add_metric import new_metric, \
    waiting_for_metric_name, waiting_for_metric_type, AddMetric, waiting_for_fill_empty_values_strategy
from handlers.get_all_metrics import get_all_metrics
from handlers.info import send_welcome
from handlers.config_metric import metric_to_config, waiting_for_fill_strategy, waiting_for_strategy_name, ConfigMetric


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start', 'help'], state='*')
    dp.register_message_handler(add_value, regexp='^#(\w+|\d)', state='*')
    dp.register_message_handler(get_all_metrics, commands=['get_metrics'], state='*')
    dp.register_message_handler(new_metric, commands=['new_metric'], state='*')
    dp.register_message_handler(waiting_for_metric_name, state=AddMetric.waiting_for_name, regexp='^[\w+]\w+')
    dp.register_callback_query_handler(waiting_for_metric_type, state=AddMetric.waiting_for_type)
    dp.register_callback_query_handler(waiting_for_fill_empty_values_strategy,
                                       state=AddMetric.waiting_for_fill_strategy)
    dp.register_message_handler(new_value_to_metric, commands=['add_value'], state='*')
    dp.register_callback_query_handler(waiting_for_name_of_metric,
                                       state=AddMetricValue.waiting_for_metric_name)
    dp.register_message_handler(waiting_for_metric_value,
                                state=AddMetricValue.waiting_for_metric_value)
    dp.register_message_handler(waiting_for_metric_value_comment,
                                state=AddMetricValue.waiting_for_metric_value_comment)
    dp.register_message_handler(set_export_options, commands=['export'])
    dp.register_message_handler(confirm_delete_warning, commands=['delete'])
    dp.register_message_handler(delete_all,
                                state=DeleteValues.waiting_for_confirm)
    dp.register_callback_query_handler(export, state=ExportStates.waiting_for_fill_empty_values_confirm)
    dp.register_message_handler(metric_to_config, commands=['config_metrics'], state='*')
    dp.register_callback_query_handler(waiting_for_strategy_name, state=ConfigMetric.waiting_for_metric_name)
    dp.register_callback_query_handler(waiting_for_fill_strategy, state=ConfigMetric.waiting_for_fill_strategy)
