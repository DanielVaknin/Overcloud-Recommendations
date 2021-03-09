import datetime
import boto3


class AWSHelpr():
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        self.client = boto3.client('ec2',
                                   aws_access_key_id=aws_access_key_id,
                                   aws_secret_access_key=aws_secret_access_key)
        self.sts = boto3.client('sts')

    def get_account_user_id(self):
        return self.sts.get_caller_identity().get('Account')

    def get_unattached_volumes(self):
        volumes = self.client.describe_volumes()
        return [volume['VolumeId'] for volume in volumes['Volumes'] if volume['State'] != "in-use"]

    def get_old_snapshots(self, days):
        owner_id = self.get_account_user_id()
        snapshots = self.client.describe_snapshots(OwnerIds=[owner_id])
        return [snapshot['SnapshotId'] for snapshot in snapshots['Snapshots']
                if (datetime.datetime.now().date() - snapshot['StartTime'].date()).days > days]

    def delete_snapshots(self, snapshots_id):
        for snapshot_id in snapshots_id:
            try:
                self.client.delete_snapshot(SnapshotId=snapshot_id)
            except Exception as e:
                if 'InvalidSnapshot.InUse' in e:
                    print(f"skipping this snapshot: {snapshots_id}")
                    continue

    def get_regions(self):
        regions = [region['RegionName'] for region in self.client.describe_regions()['Regions']]
        return regions