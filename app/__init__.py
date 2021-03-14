from flask import Flask
from app.routes import *


def create_app():
    app = Flask(__name__)

    app.register_blueprint(recommendations, url_prefix='/recommendations')

    return app
