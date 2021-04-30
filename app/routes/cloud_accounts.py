import logging

from bson.errors import InvalidId
from flask import request, jsonify, Blueprint

from app.models.Cloud_Manager import CloudManager
from app.utilities.aws_helper import *
from botocore.exceptions import ClientError

cloud_accounts = Blueprint('cloud-accounts', __name__)
logger = logging.getLogger()


@cloud_accounts.route("/validate", methods=['POST'])
def validate():
    cloud_provider = request.get_json().get('cloudProvider', None)
    credentials_obj = request.get_json().get('credentials', None)

    if credentials_obj is None:
        return jsonify({"status": "error", "error": "You must specify the 'credentials' field"}), 500

    if cloud_provider == "AWS":
        if 'accessKey' not in credentials_obj or 'secretKey' not in credentials_obj:
            return jsonify({"status": "error",
                            "error": "You must specify both 'accessKey' and 'secretKey' under 'credentials'"}), 500

        access_key = credentials_obj['accessKey']
        secret_access_key = credentials_obj['secretKey']

        try:
            AWSHelper(aws_access_key_id=access_key, aws_secret_access_key=secret_access_key)
            return jsonify({"status": "ok"})
        except ClientError as e:
            return jsonify({"status": "error", "error": e.response['Error']['Message']}), 500


@cloud_accounts.route("/billing", methods=['GET'])
def billing_date():
    cloud_account_id = request.args.get('cloud_account', None)

    if cloud_account_id is None:
        return jsonify({"status": "error", "error": "Please provide the ID of the cloud account"}), 422

    try:
        cloud_account = CloudManager.get_cloud_account_from_mongo(cloud_account_id)
        access_key = cloud_account['accessKey']
        secret_access_key = cloud_account['secretKey']

        current_bill = AWSHelper(aws_access_key_id=access_key,
                                 aws_secret_access_key=secret_access_key).get_current_bill()
        return jsonify({"status": "ok", "data": {
            "currentBill": current_bill
        }})

    except InvalidId as e:
        logger.exception(e)
        return jsonify({"status": "error", "error": "There is no recommendation with such ID"}), 404
