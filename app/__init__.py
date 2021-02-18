from os import environ
from flask import Flask
from app.routes import *


def create_app():
    app = Flask(__name__)

    app.register_blueprint(main_route, url_prefix='/recommend')

    return app