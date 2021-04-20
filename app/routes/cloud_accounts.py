import logging
from flask import request, jsonify, Blueprint
from app.utilities.aws_helper import *
from botocore.exceptions import ClientError

cloud_accounts = Blueprint('cloud-accounts', __name__)
logger = logging.getLogger()


@cloud_accounts.route("/validate", methods=['POST'])
def validate():
    cloud_provider = request.get_json().get('cloudProvider', None)
    access_key = request.get_json().get('accessKey', None)
    secret_access_key = request.get_json().get('secretKey', None)

    if cloud_provider == "AWS":
        try:
            AWSHelper(aws_access_key_id=access_key, aws_secret_access_key=secret_access_key)
            return jsonify({"status": "ok"})
        except ClientError as e:
            return jsonify({"status": "error", "error": e.response['Error']['Message']})