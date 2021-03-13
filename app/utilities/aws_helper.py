import datetime
import boto3


class AWSHelper:

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        self.access_key_id = aws_access_key_id
        self.secret_access_key = aws_secret_access_key

        base_region = 'us-east-1'

        # This is an initial client used just to get the list of all regions
        self.ec2_initial_client = self.create_boto3_client('ec2', base_region)

        self.ec2_clients = []
        for region in self.get_regions():
            self.ec2_clients.append({
                'region': region,
                'client': self.create_boto3_client('ec2', region)
            })

        self.sts = self.create_boto3_client('sts', base_region)

    def create_boto3_client(self, service, region):
        return boto3.client(service,
                            aws_access_key_id=self.access_key_id,
                            aws_secret_access_key=self.secret_access_key,
                            region_name=region)

    def get_account_user_id(self):
        return self.sts.get_caller_identity().get('Account')

    def get_unattached_volumes(self):
        unattached_volumes = []

        for client in self.ec2_clients:
            all_volumes = client['client'].describe_volumes()
            for volume in all_volumes['Volumes']:
                if volume['State'] == "available":
                    volume_data = {
                        'region': client['region'],
                        'id': volume['VolumeId'],
                        'type': volume['VolumeType'],
                        'size': volume['Size'],
                        'createTime': volume['CreateTime'].strftime("%d/%m/%Y"),
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
                        'id': snapshot['SnapshotId'],
                        'volumeId': snapshot['VolumeId'],
                        'volumeSize': snapshot['VolumeSize'],
                    }
                    old_snapshots.append(snapshot_data)

        return old_snapshots

    def get_unassociated_eip(self):
        unassociated_eip = []

        for client in self.ec2_clients:
            response = client['client'].describe_addresses()
            for address in response['Addresses']:
                allocation_id = address['AllocationId']
                if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                    eip_data = {
                        'region': client['region'],
                        'id': address['AllocationId'],
                    }
                    unassociated_eip.append(eip_data)

        return unassociated_eip

    def delete_snapshots(self, snapshots_id):
        for snapshot_id in snapshots_id:
            try:
                self.ec2_initial_client.delete_snapshot(SnapshotId=snapshot_id)
            except Exception as e:
                if 'InvalidSnapshot.InUse' in e:
                    print(f"skipping this snapshot: {snapshots_id}")
                    continue

    def get_regions(self):
        return [region['RegionName'] for region in self.ec2_initial_client.describe_regions()['Regions']]
