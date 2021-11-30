import asyncio
import time
from typing import List
import logging
from uuid import uuid4

import motor.motor_asyncio
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
print(logger.level)


class MongodbService:
    """
    Class for async CRUD document in Mongo
    """

    def __init__(self, host: str = 'localhost', port: int = 27017,
                 db: str = 'test_database', collection: str = 'test_collection'):
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


"""
USAGE
"""


async def main():
    storage = MongodbService(db='tst_db', collection='tst_collection_2')
    logging.debug(storage)

    created_docs = []
    for i in range(5):
        dto = {
            "_id": str(uuid4()),
            "payload": str(uuid4()),
            "field2": str(int(time.time()))
        }
        result = await storage.create_one(dto)
        logging.debug(f'Created doc with id: {result}')
        created_docs.append(result)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
