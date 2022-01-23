from enum import Enum


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
