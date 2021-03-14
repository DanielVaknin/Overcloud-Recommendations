from threading import Thread
from app.models.Cloud_Manager import *
from flask import request, jsonify, Blueprint

recommendations = Blueprint('recommendations', __name__)


@recommendations.route("/", methods=['GET'])
def main_route():
    cloud_account_id = request.args.get('cloud_account', None)
    recommendation_id = request.args.get('recommendation', None)
    if cloud_account_id is None:
        return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 422

    result = CloudManager.get_recommendations_for_cloud_provider(cloud_account_id, recommendation_id)
    return jsonify({"status": "ok", "recommendations": result})


@recommendations.route("/scan", methods=['POST'])
def scan():
    cloud_account_id = request.get_json().get('cloud_account', None)
    if cloud_account_id is not None:
        cloud_provider = CloudManager.cloud_provider_identify(identity=cloud_account_id)
        if cloud_provider is None:
            return jsonify({"status": "error", "error": "Cloud Provider Not Found"}), 404
        Thread(target=cloud_provider.recommend()).start()
        return jsonify({"status": "ok"})
    # TODO: Scan all cloud providers if didn't get any
    return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 404
