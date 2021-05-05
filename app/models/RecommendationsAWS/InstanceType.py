from app.utilities import mongo_helper
from app.models.Recommendation import Recommendation
import datetime


class InstanceType(Recommendation):
    def __init__(self, helper, account_id):
        super().__init__(helper, account_id)

    def scan(self):
        data = self.helper.get_rightsizing_recommendations()
        mongo_helper.insert(collection="recommendations",
                            document={"name": "Rightsizing Instances",
                                      "type": self.__class__.__name__,
                                      "accountId": self.account_id,
                                      "collectTime": datetime.datetime.now(),
                                      "totalPrice": round(self.calculate_total_savings(data), 4),
                                      "data": data})

    def calculate_total_savings(self, data):
        total_savings = 0
        for rec in data:
            total_savings += rec['currentMonthlyCost'] - rec['estimatedMonthlyCost']

        return total_savings

    def get(self):
        return mongo_helper.find_latest(collection="recommendations", query={"accountId": self.account_id,
                                                                             "type": self.__class__.__name__})

    def remediate(self):
        recommendation = self.get()
        if 'data' in recommendation:
            for item in recommendation['data']:
                self.helper.modify_instance_type(region=item['region'],
                                                 instance_id=item['instanceId'],
                                                 new_instance_type=item['recInstanceType'])
