from bson.objectid import ObjectId
from app.models.recommend_aws import *


class CloudManager():

    @staticmethod
    def cloud_provider_identify(identity):
        cloud_data = mongo_helper.find(collection="cloudaccounts", query={'_id': ObjectId(identity)})
        if cloud_data is None:
            return None
        if cloud_data['cloudProvider'] == "AWS":
            return recommend_aws(access_key=cloud_data['accessKey'], secret_key=cloud_data['secretKey'])

