import logging

from app.utilities.aws_helper import *
from app.utilities import mongo_helper

logger = logging.getLogger(__name__)


def get_total_price(data):
    """
    This function will go over all the resources in the recommendation and calculate
    the total price for all recommendations (that can be saved)
    :param data: a list of violating resources
    :return: The total price of all resources that can be saved
    """

    total_price = 0
    for item in data:
        if 'totalPrice' in item:
            total_price += float(item['totalPrice'].strip(' "'))
    return total_price


class RecommendAws:

    def __init__(self, account_id, access_key, secret_key):
        self.account_id = str(account_id)
        self.aws = AWSHelper(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        self.owner_id = self.aws.get_account_user_id()
        mongo_helper.delete_all(collection="recommendations", query={"accountId": self.account_id})

    def recommend(self):
        self.scan_unattached_volumes()
        self.scan_old_snapshots()
        self.scan_unassociated_eip()

    def scan_unattached_volumes(self):
        data = self.aws.get_unattached_volumes()
        mongo_helper.insert(collection="recommendations", document={"name": "Unattached Volumes",
                                                                    "accountId": self.account_id,
                                                                    "collectTime": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                                                                    "totalPrice": str(round(get_total_price(data), 4)),
                                                                    "data": data})

    def scan_old_snapshots(self):
        data = self.aws.get_old_snapshots(days=30)
        mongo_helper.insert(collection="recommendations", document={"name": "Old Snapshots",
                                                                    "accountId": self.account_id,
                                                                    "collectTime": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                                                                    "totalPrice": str(round(get_total_price(data), 4)),
                                                                    "data": data})

    def scan_unassociated_eip(self):
        data = self.aws.get_unassociated_eip()
        mongo_helper.insert(collection="recommendations", document={"name": "Unassociated EIPs",
                                                                    "accountId": self.account_id,
                                                                    "collectTime": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                                                                    "totalPrice": str(round(get_total_price(data), 4)),
                                                                    "data": data})
