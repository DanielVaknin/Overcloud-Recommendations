import datetime
import boto3


class AWSHelper:

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        self.ec2_clients = []

        self.client = boto3.client('ec2',
                                   aws_access_key_id=aws_access_key_id,
                                   aws_secret_access_key=aws_secret_access_key,
                                   region_name="us-east-1")

        for region in self.get_regions():
            self.ec2_clients.append({
                'region': region,
                'client': boto3.client('ec2',
                                       aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key,
                                       region_name=region)
            })

        self.sts = boto3.client('sts',
                                aws_access_key_id=aws_access_key_id,
                                aws_secret_access_key=aws_secret_access_key,
                                region_name="us-east-1")

    def get_account_user_id(self):
        return self.sts.get_caller_identity().get('Account')

    def get_unattached_volumes(self):
        unattached_volumes = []

        for client in self.ec2_clients:
            all_volumes = client['client'].describe_volumes()
            for volume in all_volumes['Volumes']:
                if volume['State'] != "in-use":
                    volume_data = {
                        'region': client['region'],
                        'id': volume['VolumeId'],
                        'size': volume['Size']
                    }
                    unattached_volumes.append(volume_data)

        return unattached_volumes

    def get_old_snapshots(self, days):
        old_snapshots = []
        owner_id = self.get_account_user_id()

        for client in self.ec2_clients:
            all_snapshots = client['client'].describe_snapshots(OwnerIds=[owner_id])
            for snapshot in all_snapshots['Snapshots']:
                if (datetime.datetime.now().date() - snapshot['StartTime'].date()).days > days:
                    snapshot_data = {
                        'region': client['region'],
                        'id': snapshot['SnapshotId']
                    }
                    old_snapshots.append(snapshot_data)

        return old_snapshots

    def delete_snapshots(self, snapshots_id):
        for snapshot_id in snapshots_id:
            try:
                self.client.delete_snapshot(SnapshotId=snapshot_id)
            except Exception as e:
                if 'InvalidSnapshot.InUse' in e:
                    print(f"skipping this snapshot: {snapshots_id}")
                    continue

    def get_regions(self):
        return [region['RegionName'] for region in self.client.describe_regions()['Regions']]