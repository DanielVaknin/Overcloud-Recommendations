import logging
from bson import ObjectId
from bson.errors import InvalidId
from flask import jsonify

from app.models.CloudAws import CloudAws
from app.utilities import *

logger = logging.getLogger()


class CloudManager:

    def __init__(self):
        self.CloudAWS = {}

    def cloud_provider_identify(self, identity):
        try:
            cloud_data = CloudManager.get_cloud_account_from_mongo(identity)
            if cloud_data is None:
                return None
            if cloud_data['cloudProvider'] == "AWS":
                return self.create_cloud_aws_instance(account_id=cloud_data['_id'],
                                                      access_key=cloud_data['accessKey'],
                                                      secret_key=cloud_data['secretKey'])
        except InvalidId as e:
            logger.exception(e)
            return jsonify({"status": "error", "error": "There is no cloud account with such ID"}), 404

    def create_cloud_aws_instance(self, account_id, access_key, secret_key):
        if account_id not in self.CloudAWS:
            self.CloudAWS[account_id] = CloudAws(account_id=account_id, access_key=access_key, secret_key=secret_key)
        return self.CloudAWS[account_id]

    @staticmethod
    def get_cloud_account_from_mongo(identity):
        cloud_data = mongo_helper.find(collection="cloudaccounts", query={'_id': ObjectId(identity)})
        return cloud_data