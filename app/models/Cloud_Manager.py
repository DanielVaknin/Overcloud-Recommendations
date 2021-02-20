from app.utilities import mongo_helper
from bson.objectid import ObjectId
from app.models.recommend_aws import *


class CloudManager():

    @staticmethod
    def cloud_provider_identify(self, identity, cloud):
        cloud_data = mongo_helper.find(db_name="OverCloud", collection="Users", query={'_id': ObjectId(identity)})
        if cloud == "AWS":
            return recommend_aws(access_key=cloud_data['AWS']['access_key'], secret_key=cloud_data['AWS']['secret_key'],
                                 region_name=cloud_data['AWS']['region'], db_name=cloud_data['db_name'])

