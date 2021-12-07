import logging

from pydantic import BaseSettings


class Settings(BaseSettings):
    telegram_token: str
    telegram_chat_id: str
    time_out: int = 3
    logging_level: int = logging.DEBUG
    mongo_host: str = 'localhost'
    mongo_port: int = 27017
    mongo_db_name: str = 'statistic'
    mongo_collection: str = 'metrics'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
