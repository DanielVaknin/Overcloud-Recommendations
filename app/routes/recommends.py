from threading import Thread
from app.models.Cloud_Manager import *
from flask import request, jsonify, Blueprint

recommends = Blueprint('recommends', __name__)


@recommends.route("/", methods=['GET'])
def main_route():
    return 'OK'


@recommends.route("/get", methods=['POST'])
def get_recommendations():
    identity = request.get_json().get('identity', None)
    if identity is None:
        return jsonify({"status": "error", "error": "Missing Cloud Account Identity"}), 422
    recommendations = CloudManager.get_recommendations_for_cloud_provider(identity)
    return jsonify({"status": "ok", "recommendations": recommendations})


@recommends.route("/scan", methods=['POST'])
def scan():
    identity = request.get_json().get('identity', None)
    if identity is None:
        return jsonify({"status": "error", "error": "Missing Cloud Account Identity"}), 422
    cloud_provider = CloudManager.cloud_provider_identify(identity=identity)
    if cloud_provider is None:
        return jsonify({"status": "error", "error": "Cloud Provider Not Found"}), 404
    Thread(target=cloud_provider.recommend()).start()
    return jsonify({"status": "ok"})
