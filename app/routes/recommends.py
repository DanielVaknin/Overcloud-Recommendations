from threading import Thread
from app.models.Cloud_Manager import *
from flask import request, jsonify, Blueprint
recommend = Blueprint('recommend', __name__)


@recommend.route("/", methods=['GET'])
def main_route():
    return 'OK'


@recommend.route("/Scan", methods=['POST'])
def scan():
    identity = request.args.get('identity', None)
    cloud = request.args.get('cloud', None)
    if any(param is None for param in (identity, cloud)):
        return jsonify({"status": "error", "error": "Missing parameters"})
    c = CloudManager.cloud_provider_identify(identity=identity, cloud=cloud)
    Thread(target=c.reccomend).start()
    return jsonify({"status": "ok"})


