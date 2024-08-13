from celery import shared_task
from .models import Order, Payment
from django.conf import settings
from django.utils import timezone
import time


@shared_task
def check_payment_status(order_id):
    pass

