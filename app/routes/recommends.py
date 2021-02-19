from flask import request, jsonify, Blueprint
recommend = Blueprint('recommend', __name__)
from app.models.Cloud_Manager import *


@recommend.route("/", methods=['GET'])
def main_route():
    return 'OK'


@recommend.route("/Scan", methods=['POST'])
def scan():
    identity = request.args.get('identity', None)
    if identity is None:
        return jsonify({"status": "error", "error": "Missing identity parameter"})
    c = CloudManager()



