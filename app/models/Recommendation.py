from abc import abstractmethod
import datetime

from app.utilities import mongo_helper


class Recommendation:

    def __init__(self, helper, account_id):
        self.helper = helper
        self.account_id = account_id

    @abstractmethod
    def scan(self):
        pass

    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def remediate(self):
        pass

    # TODO: Fix this function to better calculate the total price
    @staticmethod
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


class UnattachedVolumes(Recommendation):
    def __init__(self, helper, account_id):
        super().__init__(helper, account_id)

    def scan(self):
        data = self.helper.get_unattached_volumes()
        mongo_helper.insert(collection="recommendations",
                            document={"name": "Unattached Volumes",
                                      "type": self.__class__.__name__,
                                      "accountId": self.account_id,
                                      "collectTime": datetime.datetime.now(),
                                      "totalPrice": round(Recommendation.get_total_price(data), 4),
                                      "data": data})

    def get(self):
        return mongo_helper.find(collection="recommendations", query={"accountId": self.account_id,
                                                                      "type": self.__class__.__name__})

    def remediate(self):
        recommendation = self.get()
        if 'data' in recommendation:
            for item in recommendation['data']:
                self.helper.delete_volume(volume_id=item['id'], region=item['region'])


class OldSnapshots(Recommendation):
    def __init__(self, helper, account_id):
        super().__init__(helper, account_id)

    def scan(self):
        data = self.helper.get_old_snapshots(days=30)
        mongo_helper.insert(collection="recommendations",
                            document={"name": "Old Snapshots",
                                      "type": self.__class__.__name__,
                                      "accountId": self.account_id,
                                      "collectTime": datetime.datetime.now(),
                                      "totalPrice": round(Recommendation.get_total_price(data), 4),
                                      "data": data})

    def get(self):
        return mongo_helper.find(collection="recommendations", query={"accountId": self.account_id,
                                                                      "type": self.__class__.__name__})

    def remediate(self):
        recommendation = self.get()
        if 'data' in recommendation:
            for item in recommendation['data']:
                self.helper.delete_snapshot(snapshot_id=item['id'], region=item['region'])


class UnassociatedEIP(Recommendation):
    def __init__(self, helper, account_id):
        super().__init__(helper, account_id)

    def scan(self):
        data = self.helper.get_unassociated_eip()
        mongo_helper.insert(collection="recommendations",
                            document={"name": "Unassociated EIPs",
                                      "type": self.__class__.__name__,
                                      "accountId": self.account_id,
                                      "collectTime": datetime.datetime.now(),
                                      "totalPrice": round(Recommendation.get_total_price(data), 4),
                                      "data": data})

    def get(self):
        return mongo_helper.find(collection="recommendations", query={"accountId": self.account_id,
                                                                      "type": self.__class__.__name__})

    def remediate(self):
        recommendation = self.get()
        if 'data' in recommendation:
            for item in recommendation['data']:
                self.helper.release_eip(allocation_id=item['id'], region=item['region'])


class Rightsizing(Recommendation):
    def __init__(self, helper, account_id):
        super().__init__(helper, account_id)

    def scan(self):
        data = self.helper.get_rightsizing_recommendations()
        mongo_helper.insert(collection="recommendations",
                            document={"name": "Rightsizing Instances",
                                      "type": self.__class__.__name__,
                                      "accountId": self.account_id,
                                      "collectTime": datetime.datetime.now(),
                                      # "totalPrice": round(Recommendation.get_total_price(data), 4),
                                      "data": data})

    def get(self):
        return mongo_helper.find(collection="recommendations", query={"accountId": self.account_id,
                                                                      "type": self.__class__.__name__})

    def remediate(self):
        recommendation = self.get()
        if 'data' in recommendation:
            for item in recommendation['data']:
                self.helper.modify_instance_type(region=item['region'],
                                                 instance_id=item['instanceId'],
                                                 new_instance_type=item['recInstanceType'])
