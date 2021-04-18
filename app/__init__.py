from flask import Flask
from flask_cors import CORS
from app.routes import *


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(recommendations, url_prefix='/recommendations')

    return app
