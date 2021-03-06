import pymongo


class MongoHelper:

    def __init__(self, connection_string):
        self.mongo_client = pymongo.MongoClient(connection_string)
        self.db = self.mongo_client.OverCloud

    def insert(self, collection, document):
        return self.db[collection].insert_one(document)

    def find(self, collection, query):
        return self.db[collection].find_one(query)

    def find_latest(self, collection, query):
        return self.db[collection].find_one(query, sort=[('_id', pymongo.DESCENDING)])

    def find_all(self, collection, query):
        return self.db[collection].find(query)

    def delete_all(self, collection, query):
        return self.db[collection].delete_many(query)
