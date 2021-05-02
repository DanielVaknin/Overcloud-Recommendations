import logging
import sys

from app.models.Recommendation import Recommendation
from app.utilities import mongo_helper
from app.utilities.aws_helper import AWSHelper

logger = logging.getLogger()


class CloudAws:

    def __init__(self, account_id, access_key, secret_key):
        self.account_id = str(account_id)
        self.aws = AWSHelper(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        self.owner_id = self.aws.get_account_id()

    def validateAccount(self):
        try:
            self.aws.get_regions()
            return True, None
        except Exception as e:
            print(e)
            return False, e

    def get_recommendation_class_by_name(self, class_name):
        for rec in Recommendation.__subclasses__():
            if rec.__name__ == class_name:
                msg = f'Found class with name {class_name}'
                return rec, msg
        msg = f'Could not find class with name {class_name}'
        return None, msg

    def scanRecommendations(self, recommendation_type=None):
        if recommendation_type is not None:
            mongo_helper.delete_all(collection="recommendations", query={"accountId": self.account_id,
                                                                         "type": recommendation_type})
            recommendation_class, msg = self.get_recommendation_class_by_name(recommendation_type)
            if recommendation_class is not None:
                logger.info(msg)
                recommendation_class(helper=self.aws, account_id=self.account_id).scan()
            else:
                logger.exception(msg)
        else:
            mongo_helper.delete_all(collection="recommendations", query={"accountId": self.account_id})
            for rec in Recommendation.__subclasses__():
                rec(helper=self.aws, account_id=self.account_id).scan()

    def getRecommendations(self, recommendation_type=None):
        if recommendation_type is not None:
            getattr(sys.modules[__name__], recommendation_type).get()
        else:
            for rec in Recommendation.__subclasses__():
                rec(helper=self.aws, account_id=self.account_id).get()

    def remediateRecommendations(self, recommendation_type=None):
        if recommendation_type is not None:
            logger.info(f'Remediating recommendation of type {recommendation_type}')
            recommendation_class, msg = self.get_recommendation_class_by_name(recommendation_type)
            if recommendation_class is not None:
                logger.info(msg)
                recommendation_class(helper=self.aws, account_id=self.account_id).remediate()
            else:
                logger.exception(msg)
        else:
            for rec in Recommendation.__subclasses__():
                rec(helper=self.aws, account_id=self.account_id).remediate()
