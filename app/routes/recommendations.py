from threading import Thread

from bson import json_util
from bson.errors import InvalidId

from app.models.Cloud_Manager import *
from flask import request, jsonify, Blueprint

recommendations = Blueprint('recommendations', __name__)
logger = logging.getLogger()


@recommendations.route("", methods=['GET'])
def main_route():
    cloud_account_id = request.args.get('cloud_account', None)
    recommendation_id = request.args.get('recommendation', None)
    if cloud_account_id is None:
        return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 422

    try:
        get_cloud_account_from_mongo(cloud_account_id)
    except InvalidId as e:
        logger.exception(e)
        return jsonify({"status": "error", "error": "There is no cloud account with such ID"}), 404

    try:
        result = CloudManager.get_recommendations_for_cloud_provider(cloud_account_id, recommendation_id)
    except InvalidId as e:
        logger.exception(e)
        return jsonify({"status": "error", "error": "There is no recommendation with such ID"}), 404

    return jsonify({"status": "ok", "recommendations": json.loads(json_util.dumps(result))})


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
