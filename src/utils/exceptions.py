class NoUserMetricsError(Exception):
    def __str__(self):
        return 'Метрики не найдены!'
