from django import forms
from django.contrib.auth.forms import (
    UserChangeForm,
)
from django.utils.translation import gettext_lazy as _
from django_select2.forms import Select2MultipleWidget

from .models import BannedIP, GroupServices
from registration.models import CustomUser, Order, PromoCode


class CustomUserChangeAdminForm(UserChangeForm):
    phone_number = forms.CharField(
        label=_("Phone number"),
        widget=forms.TextInput(attrs={'id': 'id_phone_number', 'type': 'tel'})
    )

    class Meta:
        model = CustomUser
        fields = (
            "ip_address",
            "first_name",
            "last_name",
            "phone_number",
            "profile_photo",
            "role",
            "is_active",
            "last_promo_attempt",
        )

        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "profile_photo": _("Profile photo")
        }


class CustomUserChangeManagerForm(forms.ModelForm):
    phone_number = forms.CharField(
        label=_("Phone number"),
        widget=forms.TextInput(attrs={'id': 'id_phone_number', 'type': 'tel'})
    )

    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "phone_number",)

        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "profile_photo": _("Profile photo")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['readonly'] = True
        self.fields['first_name'].widget.attrs['readonly'] = True
        self.fields['last_name'].widget.attrs['readonly'] = True
        self.fields['phone_number'].widget.attrs['readonly'] = True


class CustomUserChangeModeratorForm(forms.ModelForm):
    phone_number = forms.CharField(
        label=_("Phone number"),
        widget=forms.TextInput(attrs={'id': 'id_phone_number', 'type': 'tel'})
    )

    class Meta:
        model = CustomUser
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "is_active",
        ]


class GroupServicesChangeForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.TextInput(attrs={'readonly': 'readonly'}), required=False)

    class Meta:
        model = GroupServices
        fields = ["id", 'title', "description", "is_active"]


class OrderChangeManagerForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = [
            "status",
            'moder_comment',
        ]


class BannedIPChangeForm(forms.ModelForm):

    class Meta:
        model = BannedIP
        fields = ["ip_address", "description"]


class PromoCodeChangeForm(forms.ModelForm):
    expiration_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "id": "id_expiration_date",
                'type': 'text',
                'placeholder': 'dd-mm-yyyy',
            }
        ),
    )

    class Meta:
        model = PromoCode
        fields = [
            "value",
            "description",
            "discount",
            "expiration_date",
            "is_active",
            "one_time_use",
            "used_by",
            "applicable_services",
            "applicable_categories",
        ]

        labels = {
            "value": _("Value"),
            "description": _("Description"),
            "discount": _("Discount"),
            "expiration_date": _("Expiration date"),
            "is_active": _("Active"),
        }

        widgets = {
            "used_by": Select2MultipleWidget,
            "applicable_services": Select2MultipleWidget,
            "applicable_categories": Select2MultipleWidget,
        }
