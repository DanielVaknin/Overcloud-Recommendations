import datetime
import json
from decimal import Decimal

import boto3


class AWSHelper:

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        """
        Constructor for the class. Will initialize the relevant AWS boto3 clients
        :param aws_access_key_id: "access key" for the AWS account
        :param aws_secret_access_key: "secret access key" for the AWS account
        """

        self.access_key_id = aws_access_key_id
        self.secret_access_key = aws_secret_access_key
        base_region = 'us-east-1'

        # This client is currently being used only to get the full name of all regions
        self.ssm_client = self.create_boto3_client('ssm', base_region)

        # This is an initial client used just to get the list of all regions
        self.ec2_initial_client = self.create_boto3_client('ec2', base_region)

        # Create a map of all regions and their respective EC2 client (like "client factory")
        self.ec2_clients = []
        for region in self.get_regions():
            self.ec2_clients.append({
                'region': region,
                'regionFullName': self.get_region_full_name(region),
                'client': self.create_boto3_client('ec2', region),
            })

        self.sts_client = self.create_boto3_client('sts', base_region)

        self.pricing_client = self.create_boto3_client('pricing', base_region)

    def create_boto3_client(self, service, region):
        """
        This will create a new AWS boto3 client based on the provided details
        :param service: The AWS service to create client for (for example: "ec2")
        :param region: The region to create the client in (for example: "us-east-1")
        :return: The created AWS client
        """

        return boto3.client(service,
                            aws_access_key_id=self.access_key_id,
                            aws_secret_access_key=self.secret_access_key,
                            region_name=region)

    def get_account_user_id(self):
        return self.sts_client.get_caller_identity().get('Account')

    def get_price_for_resource(self, service_code, region_full_name, filters):
        """
        This function checks the price of the specific service in AWS pricing API based on the provided filters
        :param service_code: The AWS service code (example: "AmazonEC2"
        :param region_full_name: Full name of AWS region (example: "US East (N. Virginia)")
        :param filters: List of additional filters for the query (example: [{'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'storage'}]
        :return: A dictionary containing the price and the price unit
        """

        search_filters = [{'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_full_name},
                          {'Type': 'TERM_MATCH', 'Field': 'locationType', 'Value': 'AWS Region'}]
        search_filters.extend(filters)

        pricing_response = self.pricing_client.get_products(
            ServiceCode=service_code,
            Filters=search_filters,
            MaxResults=2
        )

        try:
            respjson = json.loads(''.join(pricing_response['PriceList']))
            parse1 = respjson['terms']['OnDemand'][list(respjson['terms']['OnDemand'])[0]]
            priceDimensions = list(parse1['priceDimensions'])
            price = parse1['priceDimensions'][priceDimensions[len(priceDimensions) - 1]]['pricePerUnit']['USD']
            price_unit = parse1['priceDimensions'][priceDimensions[len(priceDimensions) - 1]]['unit']
        except Exception as e:
            return None

        return {'price': price, 'price_unit': price_unit}

    def get_unattached_volumes(self):
        """
        This function will search for all EBS volumes that are not attached to any EC2 instance
        :return: List of all EBS volumes with their details
        """

        unattached_volumes = []

        for client in self.ec2_clients:
            all_volumes = client['client'].describe_volumes()
            for volume in all_volumes['Volumes']:
                if volume['State'] == "available":
                    volume_type = volume['VolumeType']

                    volume_data = {
                        'region': client['region'],
                        'id': volume['VolumeId'],
                        'type': volume['VolumeType'],
                        'size': volume['Size'],
                        'createTime': volume['CreateTime'].strftime("%d/%m/%Y"),
                    }

                    # Get volume price
                    price = self.get_price_for_resource('AmazonEC2', client['regionFullName'], [
                        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'storage'},
                        {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': volume_type},
                    ])

                    if price is not None:
                        volume_data.update({
                            'price': price['price'],
                            'priceUnit': price['price_unit'],
                            'totalPrice': str(round(Decimal(price['price'].strip(' "')) * volume['Size'], 4)),
                        })

                    unattached_volumes.append(volume_data)

        return unattached_volumes

    def delete_volume(self, volume_id, region):
        """
        This function will delete an EBS volume in the provided region based on its' ID
        :param volume_id: ID of the volume to delete
        :param region: Region where the volume is located
        """

        for ec2_client in self.ec2_clients:
            if ec2_client['region'] == region:
                client = ec2_client['client']
                try:
                    print(f'Volume with ID {volume_id} will be deleted')
                    # client.delete_volume(VolumeId=volume_id)
                except Exception as e:
                    print(f'Failed to delete volume with ID {volume_id}')
                break

    def get_old_snapshots(self, days):
        """
        This function will search for EBS snapshots that are older then the provided number of days
        :param days: Number of days (to search for snapshots older then this number)
        :return: List of old snapshots with their details
        """

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

                    # Get snapshot price
                    # Workaround: AWS pricing API is missing snapshot pricing in regions other then N. Virginia
                    price = self.get_price_for_resource('AmazonEC2', 'US East (N. Virginia)', [
                        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Storage Snapshot'},
                        {'Type': 'TERM_MATCH', 'Field': 'usageType', 'Value': 'EBS:SnapshotUsage'},
                    ])

                    if price is not None:
                        snapshot_data.update({
                            'price': price['price'],
                            'priceUnit': price['price_unit'],
                            'totalPrice': str(round(Decimal(price['price'].strip(' "')) * snapshot['VolumeSize'], 4)),
                        })

                    old_snapshots.append(snapshot_data)

        return old_snapshots

    def delete_snapshot(self, snapshot_id, region):
        """
        This function will delete an EBS snapshot in the provided region based on its' ID
        :param snapshot_id: ID of the snapshot to delete
        :param region: Region where the snapshot is located
        """

        for ec2_client in self.ec2_clients:
            if ec2_client['region'] == region:
                client = ec2_client['client']
                try:
                    print(f'Snapshot with ID {snapshot_id} will be deleted')
                    # client.delete_snapshot(SnapshotId=snapshot_id)
                except Exception as e:
                    print(f'Failed to delete snapshot with ID {snapshot_id}')
                break

    def get_unassociated_eip(self):
        """
        This function will search for Elastic IPs that are not associated to any instance
        :return: List of unassociated EIPs
        """

        unassociated_eip = []

        for client in self.ec2_clients:
            response = client['client'].describe_addresses()
            for address in response['Addresses']:
                if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                    eip_data = {
                        'region': client['region'],
                        'id': address['AllocationId'],
                    }

                    # Get Elastic IP price
                    price = self.get_price_for_resource('AmazonEC2', client['regionFullName'], [
                        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'IP Address'},
                        {'Type': 'TERM_MATCH', 'Field': 'usageType', 'Value': 'ElasticIP:IdleAddress'},
                    ])

                    if price is not None:
                        eip_data.update({
                            'price': price['price'],
                            'priceUnit': price['price_unit'],
                            'totalPrice': str(round(Decimal(price['price'].strip(' "')), 4)),
                        })

                    unassociated_eip.append(eip_data)

        return unassociated_eip

    def release_eip(self, allocation_id, region):
        """
        This function will release an Elastic IP in the provided region based on its' ID
        :param allocation_id: Allocation ID of the Elastic IP to release
        :param region: Region where the Elastic IP with the allocation ID is located
        """

        for ec2_client in self.ec2_clients:
            if ec2_client['region'] == region:
                client = ec2_client['client']
                try:
                    print(f'Elastic IP with Allocation ID {allocation_id} will be released')
                    # client.release_address(AllocationId=allocation_id)
                except Exception as e:
                    print(f'Failed to release Elastic IP with Allocation ID {allocation_id}')
                break

    def get_regions(self):
        """
        This function will get a list of all AWS regions
        :return: List of AWS regions
        """

        return [region['RegionName'] for region in self.ec2_initial_client.describe_regions()['Regions']]

    def get_region_full_name(self, region):
        """
        This function will get the full name of a specified region (for example: "US East (N. Virginia)")
        This is being used for AWS pricing API which requires the full name of the regions for the filters.
        :param region: Short name of a region
        :return: Full name of the region
        """

        response = self.ssm_client.get_parameter(Name=f'/aws/service/global-infrastructure/regions/{region}/longName')
        region_name = response['Parameter']['Value']  # US West (N. California)
        return region_name
