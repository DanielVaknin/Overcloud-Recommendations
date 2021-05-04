import json
from threading import Thread
from bson import json_util

from app.scheduler import scheduler
from app.models import cloud_manager
from flask import request, jsonify, Blueprint
recommendations = Blueprint('recommendations', __name__)


@recommendations.route("", methods=['GET'])
def main_route():
    cloud_account_id = request.args.get('cloud_account', None)
    recommendation_type = request.args.get('recommendation_type', None)

    if cloud_account_id is not None:
        cloud_provider = cloud_manager.cloud_provider_identify(identity=cloud_account_id)
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
        cloud_provider = cloud_manager.cloud_provider_identify(identity=cloud_account_id)
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
        cloud_provider = cloud_manager.cloud_provider_identify(identity=cloud_account_id)
        if cloud_provider is None:
            return jsonify({"status": "error", "error": "Cloud Provider Not Found"}), 404

        Thread(target=cloud_provider.remediateRecommendations, kwargs={"recommendation_type": recommendation_type}).start()
        return jsonify({"status": "ok"})

    return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 404


@recommendations.route("/schedule-scan", methods=['POST'])
def schedule_scan():
    cloud_account_id = request.get_json().get('cloud_account', None)
    scan_interval = request.get_json().get('scan_interval', None)
    if cloud_account_id and scan_interval:
        cloud_provider = cloud_manager.cloud_provider_identify(identity=cloud_account_id)
        if cloud_provider is None:
            return jsonify({"status": "error", "error": "Cloud Provider Not Found"}), 404
        scheduler.add_job(func=cloud_provider.scanRecommendations, trigger="interval",
                          id=f"{cloud_account_id}", hours=scan_interval, jobstore='mongo', misfire_grace_time=3600)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 404

