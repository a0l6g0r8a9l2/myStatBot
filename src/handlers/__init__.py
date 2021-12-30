from aiogram import Dispatcher

from handlers.metric_values import new_value_to_metric, waiting_for_name_of_metric, AddMetricValue, \
    waiting_for_metric_value_comment, waiting_for_metric_value, add_value, export
from handlers.metrics import get_all_metrics, new_metric, \
    waiting_for_metric_name, waiting_for_metric_type, AddMetric
from handlers.common import send_welcome


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(send_welcome, commands=['start', 'help'], state='*')
    dp.register_message_handler(add_value, regexp='^#(\w+|\d)', state='*')
    dp.register_message_handler(get_all_metrics, commands=['get_metrics'], state='*')
    dp.register_message_handler(new_metric, commands=['new_metric'], state='*')
    dp.register_message_handler(waiting_for_metric_name, state=AddMetric.waiting_for_name, regexp='^[\w+]\w+')
    dp.register_callback_query_handler(waiting_for_metric_type, state=AddMetric.waiting_for_type)
    dp.register_message_handler(new_value_to_metric, commands=['add_value'], state='*')
    dp.register_callback_query_handler(waiting_for_name_of_metric,
                                       state=AddMetricValue.waiting_for_metric_name)
    dp.register_message_handler(waiting_for_metric_value,
                                state=AddMetricValue.waiting_for_metric_value)
    dp.register_message_handler(waiting_for_metric_value_comment,
                                state=AddMetricValue.waiting_for_metric_value_comment)
    dp.register_message_handler(export, commands=['export'])
