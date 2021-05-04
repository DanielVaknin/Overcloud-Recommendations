from abc import abstractmethod


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
                total_price += item['totalPrice']
        return total_price









