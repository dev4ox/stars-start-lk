from django.contrib.auth.forms import UserCreationForm, UserChangeForm, ReadOnlyPasswordHashField, AuthenticationForm
from .models import CustomUser, Services, Order, Category
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django import forms
from phonenumber_field.formfields import PhoneNumberField


class ServicesChangeForm(forms.ModelForm):
    class Meta:
        model = Services
        fields = ['title', "description", 'image_path']


class OrderChangeForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "user",
            "service",
            "status",
            "cost",
            "user_comment",
            'moder_comment',
        ]


class OrderAddUser(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['service', 'category', 'status', 'user_comment', 'moder_comment', 'cost']
        widgets = {
            'moder_comment': forms.HiddenInput(),  # Скрываем поле комментария модератора
            'cost': forms.HiddenInput(),  # Скрываем поле стоимости
            'status': forms.HiddenInput(),  # Скрываем поле статуса
            "service": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super(OrderAddUser, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.none()

        if 'service' in self.data:

            try:
                service_id = int(self.data.get('service'))
                self.fields['category'].queryset = Category.objects.filter(service_id=service_id).order_by('name')

            except (ValueError, TypeError):
                pass

        elif self.instance.pk:
            self.fields['category'].queryset = self.instance.service.categories.order_by('name')


class OrderReadOnlyForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['user', 'service', 'category', 'status', 'user_comment', 'moder_comment', 'cost']

    def __init__(self, *args, **kwargs):
        super(OrderReadOnlyForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['readonly'] = True
            field.widget.attrs['disabled'] = True


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label=_("Email"))
    phone_number = PhoneNumberField(
        label=_("Phone number"),
        region="RU",
        widget=forms.TextInput(attrs={'id': 'id_phone_number'})
    )
    agree_to_terms = forms.BooleanField(
        label=mark_safe(
            'I agree to the <a href="{% url \'terms_of_service\' %}" target="_blank">Terms of Service</a> '
            'and the <a href="{% url \'user_agreement\' %}" target="_blank">User Agreement</a>'
        ),
        required=True
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
    # username = forms.EmailField(label=_("Email"))
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


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254, required=True)
