from django.db import models
from registration.models import CustomUser, Order
from django.utils.translation import gettext_lazy as _


# group services model
class GroupServices(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(default="")

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
