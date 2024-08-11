from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
import os
import uuid
from django.utils.translation import gettext_lazy as _


def user_directory_path(instance, filename):
    # Function to generate the path and unique filename
    extension = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join('profile_photos/', unique_filename)


# User model
class CustomUser(AbstractUser):
    user_id = models.BigAutoField(primary_key=True)
    username = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A user with this email already exists."),
        },
    )
    phone_number = PhoneNumberField(region="RU")
    profile_photo = models.ImageField(
        upload_to=user_directory_path,
        default="profile_photos/default.png",
        null=True,
    )
    last_password_reset_request = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.username

    @staticmethod
    def get_absolute_url():
        return reverse('profile')


def catalog_directory_path(instance, filename):
    # Function to generate the path and unique filename
    extension = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join('services_images/', unique_filename)


class Category(models.Model):
    name = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    service = models.ForeignKey('Services', on_delete=models.CASCADE, related_name='categories', default="")

    def __str__(self):
        return f"{self.name} ({self.service.title})"


class Services(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(default="")
    image_path = models.ImageField(
        upload_to='services_images/',
        blank=True,
        null=True,
        default="services_images/default.jpg"
    )

    def __str__(self):
        return self.title


def order_directory_path(instance, filename):
    # Function to generate the path and unique filename
    extension = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join('order_user_tickets/', unique_filename)


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В обработке'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
        ('paid', 'Оплачен'),
        ('not_paid', "Не оплачен"),
    ]

    order_id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name=_("User"), default="")
    user_ticket_path = models.CharField(null=True, max_length=200)
    service = models.ForeignKey(Services, on_delete=models.CASCADE, default="")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default="", null=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    user_comment = models.TextField(blank=True, null=True)
    moder_comment = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return f"Order {self.order_id} by {self.user.username}"


# Payment model
class Payment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name=_("User"))
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name=_("Order"))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Amount"))
    date_payment = models.DateTimeField(auto_now=True, verbose_name=_("Date Payment"))
    trans_id = models.CharField(max_length=1000, verbose_name=_("Transaction ID"))

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"Payment {self.trans_id} by {self.user}"
