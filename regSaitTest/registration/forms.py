# python lib
import os
import time

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
from django.conf import settings
from phonenumber_field.formfields import PhoneNumberField
from tinymce.widgets import TinyMCE

# my lib
from .models import CustomUser, Services, Order, Category, PromoCode
from .utils import get_min_cost
from panels.models import GroupServices


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


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]

        else:
            result = [single_file_clean(data, initial)]

        return result


class ServicesChangeForm(forms.ModelForm):
    description = forms.CharField(
        widget=TinyMCE(
            attrs={
                'cols': 80,
                'rows': 30,
                "id": "service_form_description_textarea"
            }
        )
    )
    load_content = MultipleFileField(required=False)
    table_contents = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "hidden": True,
                "id": "panels_form_services_contents_table",
                "value": 0,
            }
        ),
        required=False
    )
    id = forms.IntegerField(required=False)

    class Meta:
        model = Services
        fields = [
            "id",
            'title',
            "group_services",
            "description",
            'image_path',
            "table_contents",
            "load_content",
            "is_active",
            "is_visible_content"
        ]

        labels = {
            "table_contents": _("Table contents")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["id"].widget.attrs["readonly"] = True
        self.fields["id"].widget.attrs["id"] = "service_id"

        if "instance" in kwargs:
            instance = kwargs["instance"]

            self.fields["id"].initial = instance.id

        else:
            self.fields["id"].initial = 0

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_files = self.cleaned_data.get('load_content')
        file_paths = []

        if instance.id:
            upload_dir = settings.MEDIA_ROOT + '\\service_contents\\' + str(instance.id)
            last_id = None

        else:
            groups_services = GroupServices.objects.all().order_by("id")
            new_service = Services.objects.create(
                title="",
                description="",
                group_services_id=groups_services[0].id,
            )

            last_id = new_service.id + 1

            new_service.delete()

            upload_dir = settings.MEDIA_ROOT + '\\service_contents\\' + str(last_id)

        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        for file in uploaded_files:
            file_path = self.handle_uploaded_file(file, upload_dir=upload_dir)

            if file_path not in instance.contents:
                file_paths.append(file_path)

        # Добавляем новые пути в contents
        if file_paths:
            instance.contents.extend(file_paths)

        if commit:
            if not last_id:
                instance.save()

            else:
                instance.save(last_id=last_id)

        return instance

    @staticmethod
    def handle_uploaded_file(f, upload_dir: str) -> str:
        file_path = os.path.join(upload_dir, f.name)

        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        return file_path


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.none()

        if 'initial' in kwargs:
            service = kwargs["initial"]["service"]

            try:
                queryset = get_min_cost(service, output_queryset=True)

                if queryset:
                    self.fields["category"].queryset = queryset

            except (ValueError, TypeError):
                pass

    promo_code = forms.CharField(max_length=20, required=False)

    class Meta:
        model = Order
        fields = [
            "user",
            'service',
            'category',
            'status',
            "promo_code",
            'user_comment',
            'moder_comment',
            'cost'
        ]

        widgets = {
            'moder_comment': forms.HiddenInput(),  # Скрываем поле комментария модератора
            'cost': forms.HiddenInput(),  # Скрываем поле стоимости
            'status': forms.HiddenInput(),  # Скрываем поле статуса
            "service": forms.HiddenInput(),
            "user": forms.HiddenInput(),
        }

        labels = {
            "category": _("Category"),
            "user_comment": _("User comment"),
            "promo_code": _("Promo code"),
        }

    def save(self, commit=True):
        order = super().save(commit=False)
        promo_code_value = self.cleaned_data.get('promo_code', '').strip()
        user = self.cleaned_data.get("user")

        try:
            if promo_code_value:
                promo_code = PromoCode.objects.get(value=promo_code_value)
                order.cost = promo_code.apply_discount(int(order.category.cost))
                promo_code.use(user)

        except PromoCode.DoesNotExist:
            pass

        if commit:
            order.save()

        return order

