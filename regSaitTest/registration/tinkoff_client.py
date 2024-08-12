import requests
from django.conf import settings
import hashlib


class TinkoffClient:
    def __init__(self, terminal_key, secret_key):
        self.terminal_key = terminal_key
        self.secret_key = secret_key
        self.base_url = 'https://secured-openapi.tbank.ru/api/v1/'

    def create_payment(self, order_id, amount, description):
        payload = {
            "TerminalKey": self.terminal_key,
            "Amount": amount,
            "OrderId": order_id,
            "Description": description,
            "SuccessURL": settings.SUCCESS_URL,
            "FailURL": settings.FAIL_URL,
            "Token": self._generate_token(order_id, amount)
        }
        print(payload)

        response = requests.post(self.base_url + 'payment/ruble-transfer/pay', json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Text: {response.text}")
        return response.json()

    def _generate_token(self, order_id, amount=None):
        data = f'{self.terminal_key}{order_id}'
        if amount is not None:
            data += f'{amount}'
        data += self.secret_key

        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def check_payment_status(self, order_id):
        payload = {
            "TerminalKey": self.terminal_key,
            "OrderId": order_id,
            "Token": self._generate_token(order_id)
        }

        response = requests.get(self.base_url + 'payment/ruble-transfer/status', params=payload)
        return response.json()
