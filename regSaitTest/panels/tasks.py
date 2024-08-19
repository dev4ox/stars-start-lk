from celery import shared_task
from yookassa import Payment, Configuration
from requests import HTTPError
from registration.models import Order
from .models import Payment as Payment_models
from django.conf import settings
from django.utils import timezone
import time


@shared_task
def check_payment_status(payment_id: str, order_id):
    order = Order.objects.get(order_id=order_id)

    timeout = 15 * 60  # 15 минут в секундах
    start_time = time.time()
    delay = 15  # sec

    Configuration.account_id = settings.YOKASSA_ACCOUNT_ID
    Configuration.secret_key = settings.YOKASSA_SECRET_KEY

    while time.time() - start_time < timeout:
        try:
            payment_to_yokassa = Payment.find_one(payment_id)

        except HTTPError as e:
            return f"Payment not found\nUser: {order.user}\nPayment_id: {payment_id}\nOrder_id: {order.order_id}"

        # print(payment_to_yokassa.json())
        if payment_to_yokassa is not None:
            if payment_to_yokassa.status == "pending":
                time.sleep(delay)

            elif payment_to_yokassa.status == "succeeded":
                payment_to_db = Payment_models.objects.create(
                    user=order.user,
                    order=order,
                    amount=order.cost,
                    date_payment=timezone.now(),
                    trans_id=payment_to_yokassa.id
                )

                order.status = "paid"
                order.save()

                return (f"Payment confirmed and processed\n"
                        f"User: {order.user}\nPayment_id: {payment_id}\nOrder_id: {order.order_id}")

            elif payment_to_yokassa.status == "waiting_for_capture":
                time.sleep(delay)

            elif payment_to_yokassa.status == "canceled":
                result_message = (f"Payment canceled\nUser: {order.user}\nPayment_id: {payment_id}\n"
                                  f"Order_id: {order.order_id}")

                return result_message

            else:
                time.sleep(delay)

    return (f"Payment not confirmed within the time limit\n"
            f"User: {order.user}\nPayment_id: {payment_id}\nOrder_id: {order.order_id}")
