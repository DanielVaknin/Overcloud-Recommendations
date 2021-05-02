import json
from threading import Thread
from bson import json_util
from app.models.Cloud_Manager import *
from flask import request, jsonify, Blueprint

recommendations = Blueprint('recommendations', __name__)


@recommendations.route("", methods=['GET'])
def main_route():
    cloud_account_id = request.args.get('cloud_account', None)
    recommendation_type = request.args.get('recommendation_type', None)

    if cloud_account_id is not None:
        cloud_provider = CloudManager.cloud_provider_identify(identity=cloud_account_id)
        if cloud_provider is None:
            return jsonify({"status": "error", "error": "Cloud Provider Not Found"}), 404

        result = cloud_provider.getRecommendations(recommendation_type)
        return jsonify({"status": "ok", "recommendations": json.loads(json_util.dumps(result))})

    return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 404


@recommendations.route("/scan", methods=['POST'])
def scan():
    cloud_account_id = request.get_json().get('cloud_account', None)
    recommendation_type = request.get_json().get('recommendation_type', None)
    if cloud_account_id is not None:
        cloud_provider = CloudManager.cloud_provider_identify(identity=cloud_account_id)
        if cloud_provider is None:
            return jsonify({"status": "error", "error": "Cloud Provider Not Found"}), 404
        Thread(target=cloud_provider.scanRecommendations, kwargs={"recommendation_type": recommendation_type}).start()
        return jsonify({"status": "ok"})

    return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 404


@recommendations.route("/remediate", methods=['POST'])
def remediate():
    cloud_account_id = request.get_json().get('cloud_account', None)
    recommendation_type = request.get_json().get('recommendation_type', None)

    if cloud_account_id is not None:
        cloud_provider = CloudManager.cloud_provider_identify(identity=cloud_account_id)
        if cloud_provider is None:
            return jsonify({"status": "error", "error": "Cloud Provider Not Found"}), 404

        Thread(target=cloud_provider.remediateRecommendations, kwargs={"recommendation_type": recommendation_type}).start()
        return jsonify({"status": "ok"})

    return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 404
