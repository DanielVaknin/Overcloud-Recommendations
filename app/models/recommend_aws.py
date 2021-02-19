import logging
from app.utilities.aws_helper import *
logger = logging.getLogger(__name__)


class reccomend_aws():

    def __init__(self, access_key, secret_key, region_name):
        self.aws = AWSHelpr(aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region_name)
        self.owner_id = self.aws.get_account_user_id()

    def reccomend(self):
        pass

    def scan_unattached_volmues(self):
        self.aws.get_unattached_volumes()

        # todo: save result in mongo

    def scan_old_snapshots(self):
        self.aws.get_old_snapshots(owner_id=self.owner_id, days=30)