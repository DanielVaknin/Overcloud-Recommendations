from flask import Flask
from app.routes import *


def create_app():
    app = Flask(__name__)

    app.register_blueprint(recommends, url_prefix='/recommends')

    return app
