import pymongo


class MongoHelper():

    def __init__(self, connection_string):
        self.mongo_client = pymongo.MongoClient(connection_string)

    def insert(self, db_name, collection, document):
        db = self.mongo_client[db_name]
        return db[collection].insert_one(document)

    def find(self, db_name, collection, query):
        db = self.mongo_client[db_name]
        return db[collection].find_one(query)