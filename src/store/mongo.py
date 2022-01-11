from typing import List

import motor.motor_asyncio
from pymongo.errors import PyMongoError

from src.config import settings
from utils import default_logger, log_it


class MongodbService:
    """
    Class for async CRUD document in Mongo
    """

    def __init__(self, host: str = settings.mongo_host, port: int = settings.mongo_port,
                 db: str = settings.mongo_db_name, collection: str = settings.mongo_collection):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(host, port)
        self._db = self._client[db]
        self._collection = self._db[collection]

    @log_it(logger=default_logger)
    async def create_one(self, dto) -> str:
        """
        Create document in Mongo

        :param dto: document
        :return: id document in Mongo
        """
        try:
            async with await self._client.start_session() as s:
                result = await self._collection.insert_one(dto, session=s)
                default_logger.debug(result.inserted_id)
                return result.inserted_id
        except PyMongoError as err:
            default_logger.error(err.args)

    @log_it(logger=default_logger)
    async def find(self, value: str, key: str = 'user_id') -> List[dict]:
        """
        Find document in Mongo

        :param value:
        :param key:
        :return: id document in Mongo
        """
        try:
            result = []
            async with await self._client.start_session() as s:
                async for doc in self._collection.find({key: {"$eq": value}}, session=s):
                    result.append(doc)
                default_logger.debug(result)
                return result
        except PyMongoError as err:
            default_logger.error(err.args)

    @log_it(logger=default_logger)
    async def delete_many(self, value: str, key: str = 'user_id') -> bool:
        """
        Delete many documents by condition
        :param value: value for some key
        :param key: key to find
        :return: True if success
        """
        try:
            async with await self._client.start_session() as s:
                await self._collection.delete_many({key: {"$eq": value}}, session=s)
                return True
        except PyMongoError as err:
            default_logger.error(err.args)
            return False

    def __repr__(self):
        return f'DB: {self._db.name} Collection: {self._collection.name}'
