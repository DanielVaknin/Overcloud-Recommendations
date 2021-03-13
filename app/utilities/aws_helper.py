import datetime
import json
from decimal import Decimal

import boto3


class AWSHelper:

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        self.access_key_id = aws_access_key_id
        self.secret_access_key = aws_secret_access_key

        base_region = 'us-east-1'

        self.ssm_client = self.create_boto3_client('ssm', base_region)

        # This is an initial client used just to get the list of all regions
        self.ec2_initial_client = self.create_boto3_client('ec2', base_region)

        self.ec2_clients = []
        for region in self.get_regions():
            self.ec2_clients.append({
                'region': region,
                'regionFullName': self.get_region_full_name(region),
                'client': self.create_boto3_client('ec2', region),
            })

        self.sts = self.create_boto3_client('sts', base_region)

        self.pricing_client = self.create_boto3_client('pricing', base_region)

    def create_boto3_client(self, service, region):
        return boto3.client(service,
                            aws_access_key_id=self.access_key_id,
                            aws_secret_access_key=self.secret_access_key,
                            region_name=region)

    def get_account_user_id(self):
        return self.sts.get_caller_identity().get('Account')

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
        respjson = json.loads(''.join(pricing_response['PriceList']))
        parse1 = respjson['terms']['OnDemand'][list(respjson['terms']['OnDemand'])[0]]
        price = parse1['priceDimensions'][list(parse1['priceDimensions'])[0]]['pricePerUnit']['USD']
        price_unit = parse1['priceDimensions'][list(parse1['priceDimensions'])[0]]['unit']

        return {'price': price, 'price_unit': price_unit}

    def get_unattached_volumes(self):
        unattached_volumes = []

        for client in self.ec2_clients:
            all_volumes = client['client'].describe_volumes()
            for volume in all_volumes['Volumes']:
                if volume['State'] == "available":
                    volume_type = volume['VolumeType']

                    # Get volume price
                    price = self.get_price_for_resource('AmazonEC2', client['regionFullName'], [
                        {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'storage'},
                        {'Type': 'TERM_MATCH', 'Field': 'volumeApiName', 'Value': volume_type},
                    ])

                    volume_data = {
                        'region': client['region'],
                        'id': volume['VolumeId'],
                        'type': volume['VolumeType'],
                        'size': volume['Size'],
                        'createTime': volume['CreateTime'].strftime("%d/%m/%Y"),
                        'price': price['price'],
                        'priceUnit': price['price_unit'],
                        'calculatedPrice': str(round(Decimal(price['price'].strip(' "')) * volume['Size'], 2)),
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
                        'pricePerHour': 0.005
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

    def get_region_full_name(self, region):
        response = self.ssm_client.get_parameter(Name=f'/aws/service/global-infrastructure/regions/{region}/longName')
        region_name = response['Parameter']['Value']  # US West (N. California)
        return region_name
