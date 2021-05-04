from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient

from app.routes import *
from apscheduler.jobstores.mongodb import MongoDBJobStore
from flask_apscheduler import APScheduler
from app.utilities import mongo_helper
from .scheduler import scheduler


class Config:
    """App configuration."""
    client = MongoClient("mongodb+srv://admin:HMQrrUjrqpnYNJ4R@cluster0.0d9xj.mongodb.net")

    SCHEDULER_JOBSTORES = {"mongo": MongoDBJobStore(client=client, database="OverCloud")}
    SCHEDULER_EXECUTORS = {"default": {"type": "threadpool", "max_workers": 20}}

    SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 3}
    SCHEDULER_API_ENABLED = True


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(recommendations, url_prefix='/recommendations')
    app.register_blueprint(cloud_accounts, url_prefix='/cloud-accounts')
    app.config.from_object(Config())
    scheduler.init_app(app)
    scheduler.start()

    return app
