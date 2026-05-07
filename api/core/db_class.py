import logging
import os

import pymongo
from bson.objectid import ObjectId


class MongoDBHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBHandler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        self.logger = logging.getLogger(__name__)

        mongo_host = os.getenv('MONGO_HOST', 'tarot-mongo')
        self.client = pymongo.MongoClient(mongo_host)
        self.db = self.client[os.getenv('MONGO_DB', 'tarot_cards_db')]

    def get_db(self):
        return self.db

    def select(self, collection: str, condition_field: str, condition_value, single: bool = False, logic: object = "and"):
        return self.db[collection].find_one({condition_field: condition_value})

    def insert(self, collection: str, data: dict) -> int:
        res = self.db[collection].insert_one(data)
        if res.acknowledged:
            return res.inserted_id
        return 0

    def update(self, collection: str, data: dict, condition_field: str = None, condition_value=None, object_id: str = None):
        if not object_id and (not condition_value or not condition_field):
            raise Exception('Condition not set properly.')
        if object_id:
            condition_field = '_id'
            condition_value = ObjectId(object_id)
        try:
            self.db[collection].update_one({condition_field: condition_value}, {"$set": data})
            return True
        except Exception as e:
            self.logger.error(f"Error updating record: {e}")
            return False

    def close_connection(self):
        self.client.close()
