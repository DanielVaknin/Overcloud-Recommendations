import datetime
import json
import boto3


class AWSHelper:
    BASE_REGION = 'us-east-1'
    REGIONS_MAP = {
        'us-east-1': 'US East (N. Virginia)',
        'us-east-2': 'US East (Ohio)',
        'us-west-1': 'US West (N. California)',
        'us-west-2': 'US West (Oregon)',
        'eu-north-1': 'Europe (Stockholm)',
        'eu-west-1': 'Europe (Ireland)',
        'eu-west-2': 'Europe (London)',
        'eu-west-3': 'Europe (Paris)',
        'eu-central-1': 'Europe (Frankfurt)',
        'ap-northeast-3': 'Asia Pacific (Osaka)',
        'ap-northeast-2': 'Asia Pacific (Seoul)',
        'ap-northeast-1': 'Asia Pacific (Tokyo)',
        'ap-south-1': 'Asia Pacific (Mumbai)',
        'ap-southeast-1': 'Asia Pacific (Singapore)',
        'ap-southeast-2': 'Asia Pacific (Sydney)',
        'sa-east-1': 'South America (Sao Paulo)',
        'ca-central-1': 'Canada (Central)',
    }

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None):
        """
        Constructor for the class. Will initialize the relevant AWS boto3 clients
        :param aws_access_key_id: "access key" for the AWS account
        :param aws_secret_access_key: "secret access key" for the AWS account
        """

        self.access_key_id = aws_access_key_id
        self.secret_access_key = aws_secret_access_key

        # This client is currently being used only to get the full name of all regions
        self.ssm_client = self.create_boto3_client('ssm', self.BASE_REGION)

        # This is an initial client used just to get the list of all regions
        self.ec2_initial_client = self.create_boto3_client('ec2', self.BASE_REGION)

        # Not used anymore as we hardcode the regions to save time
        # self.regions_map = self.map_regions_id_to_name()

        # Create a map of all regions and their respective EC2 client (like "client factory")
        self.ec2_clients = []
        for region in self.get_regions():
            self.ec2_clients.append({
                'region': region,
                'regionFullName': self.REGIONS_MAP[region],
                'client': self.create_boto3_client('ec2', region),
            })

        self.sts_client = self.create_boto3_client('sts', self.BASE_REGION)
        self.pricing_client = self.create_boto3_client('pricing', self.BASE_REGION)
        self.cost_explorer_client = self.create_boto3_client('ce', self.BASE_REGION)

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

    def get_account_id(self):
        """
        This function will get the AWS account ID
        :return: AWS account ID
        """

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

            return {'price': round(float(price), 4), 'price_unit': price_unit}
        except Exception as e:
            return None

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
                            'totalPrice': price['price'] * volume['Size'],
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
                    client.delete_volume(VolumeId=volume_id)
                except Exception as e:
                    print(f'Failed to delete volume with ID {volume_id}. Error: {e.response["Error"]["Message"]}')
                break

    def get_old_snapshots(self, days):
        """
        This function will search for EBS snapshots that are older then the provided number of days
        :param days: Number of days (to search for snapshots older then this number)
        :return: List of old snapshots with their details
        """

        old_snapshots = []
        owner_id = self.get_account_id()

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
                            'totalPrice': price['price'] * snapshot['VolumeSize'],
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
                    print(f'Failed to delete snapshot with ID {snapshot_id}. Error: {e.response["Error"]["Message"]}')
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
                            'totalPrice': round(price['price'] * 24 * 30, 4),
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
                    print(
                        f'Failed to release Elastic IP with Allocation ID {allocation_id}. Error: {e.response["Error"]["Message"]}')
                break

    def get_rightsizing_recommendations(self):
        """
        This function will get all instance rightsizing recommendations from the AWS account
        :return: List of rightsizing recommendations
        """

        # TODO: Add filter for instance ID as this function will also get instances that might not exist anymore so
        #  we can maybe first get all instances and then filter only those IDs
        response = self.cost_explorer_client.get_rightsizing_recommendation(
            # Filter={
            #     'Dimensions': {
            #         'Key': 'REGION',
            #         'Values': [
            #             'us-east-1',
            #         ],
            #     },
            # },
            Configuration={
                'RecommendationTarget': 'CROSS_INSTANCE_FAMILY',
                'BenefitsConsidered': True
            },
            Service='AmazonEC2',
        )

        recommendations = []

        for rec in response['RightsizingRecommendations']:
            currentInstance = rec['CurrentInstance']
            rec_instance_details = rec['ModifyRecommendationDetail']['TargetInstances'][0]

            recommendation = {
                'instanceId': currentInstance['ResourceId'],
                'currentInstanceType': currentInstance['ResourceDetails']['EC2ResourceDetails']['InstanceType'],
                'currentMonthlyCost': round(float(currentInstance['MonthlyCost']), 4),
                'recInstanceType': rec_instance_details['ResourceDetails']['EC2ResourceDetails']['InstanceType'],
                'estimatedMonthlyCost': round(float(rec_instance_details['EstimatedMonthlyCost']), 4)
            }

            # Get region id
            current_region = currentInstance['ResourceDetails']['EC2ResourceDetails']['Region']

            # Workaround for Europe regions as their full name is Europe but appears here as EU
            if current_region.startswith('EU'):
                current_region = current_region.replace('EU', 'Europe')

            for key, value in self.REGIONS_MAP.items():
                if value == current_region:
                    recommendation['region'] = key
                    break

            # Get createdBy tag
            for tag in currentInstance['Tags']:
                if tag['Key'] == 'aws:createdBy':
                    recommendation['createdBy'] = tag['Values'][0]

            recommendations.append(recommendation)

        return recommendations

    def modify_instance_type(self, region, instance_id, new_instance_type):
        """
        This function will modify the instance type of a given instance
        :param region: The region of the instance
        :param instance_id: The ID of the instance
        :param new_instance_type: The new instance type to modify to
        """

        for ec2_client in self.ec2_clients:
            if ec2_client['region'] == region:
                client = ec2_client['client']
                try:
                    # Get instance state
                    instance_status_response = client.describe_instance_status(InstanceIds=[instance_id])
                    instance_state = instance_status_response['InstanceStatuses'][0]['InstanceState']['Name']
                    print(f'Current instance state: {instance_state}')

                    # Stop the instance
                    if instance_state == 'running':
                        print(f'Stopping instance with ID: {instance_id}')
                        # client.stop_instances(InstanceIds=[instance_id])
                        # waiter = client.get_waiter('instance_stopped')
                        # waiter.wait(InstanceIds=[instance_id])

                    # Change the instance type
                    print(f'Changing instance type to: {new_instance_type}')
                    # client.modify_instance_attribute(InstanceId=instance_id, Attribute='instanceType',
                    #                                  Value=new_instance_type)

                    # Start the instance
                    if instance_state == 'running':
                        print(f'Starting instance with ID: {instance_id}')
                        # client.start_instances(InstanceIds=[instance_id])
                except Exception as e:
                    print(
                        f'Failed to modify instance type of instance with ID {instance_id}. Error: {e.response["Error"]["Message"]}')
                break

    def get_regions(self):
        """
        This function will get a list of all AWS regions
        :return: List of AWS regions
        """

        return [region['RegionName'] for region in self.ec2_initial_client.describe_regions()['Regions']]

    # Not used anymore as we hardcode the regions to save time
    def get_region_full_name(self, region):
        """
        This function will get the full name of a specified region (for example: "US East (N. Virginia)")
        This is being used for AWS pricing API which requires the full name of the regions for the filters.
        :param region: Short name of a region
        :return: Full name of the region
        """

        response = self.ssm_client.get_parameter(Name=f'/aws/service/global-infrastructure/regions/{region}/longName')
        region_name = response['Parameter']['Value']  # Example: US West (N. California)
        return region_name

    # Not used anymore as we hardcode the regions to save time
    def map_regions_id_to_name(self):
        regions = {}

        for region in self.get_regions():
            regions[region] = self.get_region_full_name(region)

        return regions

    def get_current_bill(self):
        response = self.cost_explorer_client.get_cost_and_usage(
            TimePeriod={
                'Start': datetime.datetime.today().replace(day=1).strftime("%Y-%m-%d"),  # Beginning of the month
                'End': datetime.datetime.now().strftime("%Y-%m-%d")
            },
            Granularity='MONTHLY',
            Metrics=[
                'AmortizedCost',
            ]
        )

        return response['ResultsByTime'][0]['Total']['AmortizedCost']['Amount']  # Total amount

    # will be called on pickling
    def __getstate__(self):
        state = self.__dict__.copy()
        del state['ssm_client']  # remove the unpicklable ssl_context
        del state['ec2_initial_client']
        del state['ec2_clients']
        del state['sts_client']
        del state['pricing_client']
        del state['cost_explorer_client']
        return state

    # will be called on unpickling
    def __setstate__(self, state):
        self.__dict__.update(state)
        self.ssm_client = self.create_boto3_client('ssm', self.BASE_REGION)  # recreate the ssl_context
        self.ec2_initial_client = self.create_boto3_client('ec2', self.BASE_REGION)

        # Create a map of all regions and their respective EC2 client (like "client factory")
        self.ec2_clients = []
        for region in self.get_regions():
            self.ec2_clients.append({
                'region': region,
                'regionFullName': self.REGIONS_MAP[region],
                'client': self.create_boto3_client('ec2', region),
            })

        self.sts_client = self.create_boto3_client('sts', self.BASE_REGION)
        self.pricing_client = self.create_boto3_client('pricing', self.BASE_REGION)
        self.cost_explorer_client = self.create_boto3_client('ce', self.BASE_REGION)
