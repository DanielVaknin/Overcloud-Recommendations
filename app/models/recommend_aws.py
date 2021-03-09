import logging
from app.utilities.aws_helper import *
from app.utilities import mongo_helper
logger = logging.getLogger(__name__)


class recommend_aws():

    def __init__(self, access_key, secret_key):
        self.aws = AWSHelpr(aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        self.owner_id = self.aws.get_account_user_id()

    def recommend(self):
        self.scan_unattached_volmues()
        self.scan_old_snapshots()

    def scan_unattached_volmues(self):
        vol_ids = self.aws.get_unattached_volumes()
        mongo_helper.insert(collection="Recommends", document={"volumes_unattached": vol_ids})

    def scan_old_snapshots(self):
        snapshots_id = self.aws.get_old_snapshots(days=30)
        mongo_helper.insert(collection="Recommends", document={"old_snapshots": snapshots_id})

