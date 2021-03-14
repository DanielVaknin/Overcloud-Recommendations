from bson import ObjectId

from app.models.recommend_aws import *
from app.utilities import *


class CloudManager:

    @staticmethod
    def cloud_provider_identify(identity):
        cloud_data = mongo_helper.find(collection="cloudaccounts", query={'_id': ObjectId(identity)})
        if cloud_data is None:
            return None
        if cloud_data['cloudProvider'] == "AWS":
            return RecommendAws(account_id=cloud_data['_id'], access_key=cloud_data['accessKey'], secret_key=cloud_data['secretKey'])

    @staticmethod
    def get_recommendations_for_cloud_provider(cloud_account_id, recommendation_id=None):
        if recommendation_id is None:
            result = mongo_helper.find_all(collection='recommendations', query={'accountId': cloud_account_id})
        else:
            result = mongo_helper.find_all(collection='recommendations', query={'accountId': cloud_account_id, '_id': ObjectId(recommendation_id)})
        return [rec for rec in result]
