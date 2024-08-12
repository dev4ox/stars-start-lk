from celery import shared_task
from .models import Order, Payment
from .tinkoff_client import TinkoffClient
from django.conf import settings
from django.utils import timezone
import time


@shared_task
def check_payment_status(order_id):
    order = Order.objects.get(id=order_id)

    tinkoff_client = TinkoffClient(
        terminal_key=settings.TINKOFF_TERMINAL_KEY,
        secret_key=settings.TINKOFF_SECRET_KEY
    )

    timeout = 15 * 60  # 15 минут в секундах
    start_time = time.time()

    while time.time() - start_time < timeout:
        status = tinkoff_client.check_payment_status(order.order_id)

        if status == 'CONFIRMED':
            order.status = 'paid'
            order.save()

            # Сохраняем информацию о платеже
            payment = Payment.objects.create(
                user=order.user,
                order=order,
                amount=order.cost,
                date_payment=timezone.now(),
                trans_id=status.get('PaymentId')
            )

            return "Payment confirmed and processed"

        # Ждем 30 секунд перед следующей проверкой
        time.sleep(30)

    return "Payment not confirmed within the time limit"

