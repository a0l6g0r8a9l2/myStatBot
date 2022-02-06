import datetime
from enum import Enum
from typing import Optional


class ConfirmOptions(Enum):
    TRUE = 'Подтверждаю'
    FALSE = 'Отмена'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, ConfirmOptions))


class FillMetricValueStrategy(Enum):
    ZERO = 'ноль'
    MEAN = 'среднее значение'
    MODE = 'модальное значение (самое частое)'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, FillMetricValueStrategy))


class MetricTypes(Enum):
    absolute = 'количественная'
    relative = 'качественная'

    @staticmethod
    def list():
        return list(map(lambda c: c.value, MetricTypes))


class DateOptions(Enum):
    TODAY = 'сегодня'
    YESTERDAY = 'вчера'
    DAY_BEFORE_YESTERDAY = 'позавчера'

    @staticmethod
    def values():
        return list(map(lambda c: c.value, DateOptions))

    @staticmethod
    def names():
        return list(map(lambda c: c.name, DateOptions))

    @staticmethod
    def enum_date():
        return list(map(date_option_to_date, DateOptions.names()))


def date_option_to_date(value: str) -> Optional[str]:
    enum_date_dict = {
        'TODAY': datetime.datetime.today().isoformat(),
        'YESTERDAY': (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat(),
        'DAY_BEFORE_YESTERDAY': (datetime.datetime.now() - datetime.timedelta(hours=48)).isoformat()
    }
    return enum_date_dict.get(value)
