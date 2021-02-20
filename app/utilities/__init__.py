from os import environ

from app.utilities.mongo_helper import *

mongo_helper = MongoHelper(environ.get("MONGO_CONNECTION_STRING"))