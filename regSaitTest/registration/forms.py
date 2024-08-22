# pip lib
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    ReadOnlyPasswordHashField,
    AuthenticationForm,
    SetPasswordForm,
)
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django import forms
from django.db import models
from phonenumber_field.formfields import PhoneNumberField

# my lib
from .models import CustomUser, Services, Order, Category
from .utils import get_min_cost


# user forms
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label=_("Email"))
    phone_number = PhoneNumberField(
        label=_("Phone number"),
        region="RU",
        widget=forms.TextInput(attrs={'id': 'id_phone_number'})
    )
    agree_to_terms = forms.BooleanField(
        label=mark_safe(_('I agree to the <a href="/lk/terms_of_service" target="_blank">Terms of service</a> and the '
                        '<a href="/lk/user_agreement" target="_blank">User agreement</a>')),
        required=True,
    )

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name")
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        new_order = [  # Creating a new ordered dictionary for fields
            ("email", self.fields.pop("email")),
            ("phone_number", self.fields.pop("phone_number")),
        ]

        # Adding remaining fields
        for field_name, field in self.fields.items():
            new_order.append((field_name, field))

        # Reassigning an ordered dictionary of fields to a form
        self.fields = dict(new_order)

        self.fields["email"].initial = self.instance.username
        self.fields["phone_number"].initial = self.instance.phone_number

    def save(self, commit=True):
        self.instance.username = self.cleaned_data["email"]
        self.instance.phone_number = self.cleaned_data["phone_number"]

        return super().save(commit=True)


class CustomUserChangeForm(UserChangeForm):
    phone_number = forms.CharField(
        label=_("Phone number"),
        widget=forms.TextInput(attrs={'id': 'id_phone_number', 'type': 'tel'})
    )
    password = ReadOnlyPasswordHashField(
        label=_("Password"),
        help_text=_(
            "Raw passwords are not stored, so there is no way to see this "
            "user’s password, but you can change the password using "
            '<a href="/password_change">this form</a>.'
        ),
    )

    class Meta:
        model = CustomUser
        fields = ("first_name", "last_name", "phone_number", "profile_photo")
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "profile_photo": _("Profile photo")
        }


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label=_("Email"))


# password forms
class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254, required=True)


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text="",
    )


class CategoryChangeForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ["name", "cost", "service", "is_active"]


class ServicesChangeForm(forms.ModelForm):
    class Meta:
        model = Services
        fields = ['title', "description", 'image_path', "group_services", "is_active"]


class OrderChangeForm(forms.ModelForm):
    manager = forms.ModelChoiceField(queryset=CustomUser.objects.filter(role=1), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cost'].widget.attrs['readonly'] = True

        if 'instance' in kwargs:
            instance = kwargs['instance']

            if instance.manager:
                # Если manager установлен, убираем пустую строку
                self.fields['manager'].empty_label = None

            else:
                # Если manager не установлен, добавляем пустую строку
                self.fields['manager'].empty_label = "--------"

            # Добавляем аннотацию для приоритета текущего менеджера
            self.fields['manager'].queryset = CustomUser.objects.filter(role=1).annotate(
                is_current_manager=models.Case(
                    models.When(username=instance.manager, then=1),
                    default=0,
                    output_field=models.IntegerField()
                )
            ).order_by('-is_current_manager', 'username')  # Сначала текущий менеджер, затем остальные по имени

    class Meta:
        model = Order
        fields = [
            "user",
            "manager",
            "service",
            "category",
            "cost",
            "status",
            "user_comment",
            'moder_comment',
        ]


class OrderAddUser(forms.ModelForm):

    class Meta:
        model = Order
        fields = [
            'service',
            'category',
            'status',
            'user_comment',
            'moder_comment',
            'cost'
        ]

        widgets = {
            'moder_comment': forms.HiddenInput(),  # Скрываем поле комментария модератора
            'cost': forms.HiddenInput(),  # Скрываем поле стоимости
            'status': forms.HiddenInput(),  # Скрываем поле статуса
            "service": forms.HiddenInput(),
        }

        labels = {
            "category": _("Category"),
            "user_comment": _("User comment"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.none()

        if 'initial' in kwargs:
            service = kwargs["initial"]["service"]

            try:
                self.fields["category"].queryset = get_min_cost(service, output_queryset=True)

            except (ValueError, TypeError):
                pass
