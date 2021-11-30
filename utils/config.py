from pydantic import BaseSettings


class Settings(BaseSettings):
    telegram_token: str
    telegram_chat_id: str
    time_out: int = 5
    mongo_host: str = 'mongodb'
    mongo_port: int = 27017
    mongo_db_name: str = 'statistic'
    mongo_collection: str = 'metrics'
