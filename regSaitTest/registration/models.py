# python lib
import os
import uuid
from glob import glob
from pathlib import Path

# pip lib
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from tinymce.models import HTMLField

# my lib
# from .tasks import check_service_contents_path


def user_directory_path(instance, filename):
    # Function to generate the path and unique filename
    extension = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join('profile_photos/', unique_filename)


# User model
class CustomUser(AbstractUser):
    ip_address = models.GenericIPAddressField(null=True, default="")
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
    promo_attempts = models.IntegerField(default=5)
    last_promo_attempt = models.DateTimeField(null=True, blank=True)

    def reset_promo_attempts(self):
        self.promo_attempts = 0
        self.last_promo_attempt = timezone.now()
        self.save()

    def increment_promo_attempts(self):
        self.promo_attempts += 1
        self.last_promo_attempt = timezone.now()
        self.save()

    def is_promo_blocked(self, block_duration):
        if self.promo_attempts >= 3 and self.last_promo_attempt:
            if timezone.now() - self.last_promo_attempt < block_duration:
                return True

            else:
                self.reset_promo_attempts()

        return False

    def __str__(self):
        return self.username

    @staticmethod
    def get_absolute_url():
        return reverse('profile')


class Category(models.Model):
    name = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    service = models.ForeignKey('Services', on_delete=models.CASCADE, related_name='categories', default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.service.title})"


def catalog_directory_path(instance, filename):
    # Function to generate the path and unique filename
    extension = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join('services_images/', unique_filename)


def content_directory_path(instance, filename):
    # Function to generate the path and unique filename
    extension = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4()}.{extension}"
    return os.path.join('service_contents/', unique_filename)


class Services(models.Model):
    title = models.CharField(max_length=255)
    description = HTMLField(default="")
    image_path = models.ImageField(
        upload_to=catalog_directory_path,
        blank=True,
        null=True,
        default="services_images/default.jpg"
    )
    group_services = models.ForeignKey("GroupServices", on_delete=models.CASCADE, default="")
    contents = models.JSONField(default=list, null=True,
                                blank=True)  # Поле для хранения списка путей к файлам в формате JSON
    is_active = models.BooleanField(default=True)
    is_visible_content = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        file_paths_on_server = []

        # Определяем путь к содержимому на сервере в зависимости от наличия параметра "last_id"
        if "last_id" in kwargs:
            path_to_contents_on_server = os.path.join(settings.MEDIA_ROOT, "service_contents", str(kwargs["last_id"]))

        else:
            path_to_contents_on_server = os.path.join(settings.MEDIA_ROOT, "service_contents", str(self.id))

        # Типы файлов, которые нужно учитывать
        file_types = [".docx", ".pdf", ".mp3", ".mp4"]

        # Собираем все файлы на сервере, соответствующие указанным типам файлов
        for file_type in file_types:
            file_paths_on_server += glob(path_to_contents_on_server + "\\*" + file_type)

        # Проверяем и корректируем содержимое contents
        self.contents: list  # Указываем, что contents является списком

        # Удаляем из contents пути, которые не существуют на сервере
        for index_content_path, content_path in enumerate(self.contents):
            if content_path not in file_paths_on_server:
                del self.contents[index_content_path]

        # Добавляем в contents файлы, которые есть на сервере, но отсутствуют в списке contents
        for file_path in file_paths_on_server:
            if file_path not in self.contents:
                self.contents.append(file_path)

        # Убираем параметр "last_id" перед сохранением объекта
        if "last_id" in kwargs:
            del kwargs["last_id"]
            super().save(*args, **kwargs)

        else:
            super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        # Если есть содержимое, определяем путь к директории, где хранятся файлы
        if self.contents:
            directory_path = Path(list(self.contents)[0]).parent

        else:
            directory_path = None

        # Удаляем все файлы, указанные в contents
        for file_path in self.contents:
            if os.path.exists(file_path):
                os.remove(file_path)

        # Если директория существует и пуста, удаляем её
        if directory_path and os.path.exists(directory_path) and not os.listdir(directory_path):
            os.rmdir(directory_path)

        super().delete(using, keep_parents)

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
    manager = models.CharField(max_length=50, default="", null=True)
    user_ticket_path = models.CharField(null=True, max_length=200)
    service = models.ForeignKey(Services, on_delete=models.CASCADE, default="")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default="", null=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    user_comment = models.TextField(blank=True, null=True)
    moder_comment = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.IntegerField(default=0)

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    def __str__(self):
        return f"Order {self.order_id} by {self.user.username}"


class PromoCode(models.Model):
    value = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    discount = models.IntegerField(default=0)  # Процент скидки
    expiration_date = models.DateField(verbose_name="Promo Code Expiration Date")
    is_active = models.BooleanField(default=True)
    one_time_use = models.BooleanField(default=True)  # Промо-код одноразовый
    used_by = models.ManyToManyField(CustomUser, blank=True,
                                     related_name='used_promo_codes')  # Пользователи, которые использовали промо-код
    applicable_services = models.ManyToManyField(Services, blank=True)  # Применимо к конкретным услугам
    applicable_categories = models.ManyToManyField(Category, blank=True)  # Применимо к конкретным категориям

    def is_valid(self, user, service, category):
        """Проверка валидности промо-кода"""
        if not self.is_active:
            return False

        if self.expiration_date < timezone.now().date():
            return False

        if self.one_time_use and user in self.used_by.all():
            return False

        if service not in self.applicable_services.all():
            return False

        if category not in self.applicable_categories.all():
            return False

        return True

    def apply_discount(self, original_cost):
        """Применение скидки к стоимости"""
        discount_amount = original_cost * (self.discount / 100)

        return original_cost - discount_amount

    def use(self, user):
        """Помечаем промо-код как использованный пользователем"""
        self.used_by.add(user)

        if self.one_time_use:
            self.is_active = False

        self.save()

    def __str__(self):
        return self.value


# group services model
class GroupServices(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(default="")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


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


# banned ip
class BannedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    description = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.ip_address) + "\n" + str(self.description)
