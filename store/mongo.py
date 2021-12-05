import logging
from typing import List

import motor.motor_asyncio
from pymongo.errors import PyMongoError

from config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.logging_level,
                    format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")


class MongodbService:
    """
    Class for async CRUD document in Mongo
    """

    def __init__(self, host: str = settings.mongo_host, port: int = settings.mongo_port,
                 db: str = settings.mongo_db_name, collection: str = settings.mongo_collection):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(host, port)
        self._db = self._client[db]
        self._collection = self._db[collection]

    async def create_one(self, dto) -> str:
        """
        Create document in Mongo

        :param dto: document
        :return: id document in Mongo
        """
        try:
            async with await self._client.start_session() as s:
                result = await self._collection.insert_one(dto, session=s)
                logger.debug(result.inserted_id)
                return result.inserted_id
        except PyMongoError as err:
            logging.error(err.args)

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
                logger.debug(result)
                return result
        except PyMongoError as err:
            logging.error(err.args)

    def __repr__(self):
        return f'DB: {self._db.name} Collection: {self._collection.name}'
