import logging
from app.utilities.aws_helper import *
from app.utilities import mongo_helper
logger = logging.getLogger(__name__)


class RecommendAws:

    def __init__(self, access_key, secret_key):
        self.aws = AWSHelper(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        self.owner_id = self.aws.get_account_user_id()
        mongo_helper.delete_all(collection="Recommends")

    def recommend(self):
        self.scan_unattached_volumes()
        self.scan_old_snapshots()

    def scan_unattached_volumes(self):
        data = self.aws.get_unattached_volumes()
        mongo_helper.insert(collection="Recommends", document={"collect_time": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                                                               "unattached_volumes": data})

    def scan_old_snapshots(self):
        data = self.aws.get_old_snapshots(days=30)
        mongo_helper.insert(collection="Recommends", document={"collect_time": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S"),
                                                               "old_snapshots": data})

