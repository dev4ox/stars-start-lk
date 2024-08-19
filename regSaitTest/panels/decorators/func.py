from functools import wraps
from typing import Callable

from django import forms

from registration.models import CustomUser, Order, Services, Category
from registration.forms import CustomUserChangeForm, ServicesChangeForm, CategoryChangeForm, OrderChangeForm
from ..models import BannedIP, GroupServices
from ..forms import (
    BannedIPChangeForm,
    GroupServicesChangeForm,
    CustomUserChangeAdminForm,
    CustomUserChangeManagerForm,
    OrderChangeManagerForm,
    CustomUserChangeModeratorForm,
)


def panels_form_sub_data(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        args = list(args)
        request = args[0]

        default_title = "Title"
        default_h2_tag = "H2_tag"

        forms_change = {
            "user_change": CustomUserChangeForm,
            "user_admin_change": CustomUserChangeAdminForm,
            "user_manager_change": CustomUserChangeManagerForm,
            "user_moderator_change": CustomUserChangeModeratorForm,
            "group_service_change": GroupServicesChangeForm,
            "service_change": ServicesChangeForm,
            "category_change": CategoryChangeForm,
            "order_change": OrderChangeForm,
            "order_manager_change": OrderChangeManagerForm,
            "banned_ip_change": BannedIPChangeForm,
        }

        form_widgets = {
            "hidden_input": forms.HiddenInput()
        }

        models = {
            "custom_user": CustomUser,
            "group_service": GroupServices,
            "services": Services,
            "category": Category,
            "order": Order,
            "banned_ip": BannedIP,
        }

        request.forms_change = forms_change
        request.form_widgets = form_widgets
        request.models = models
        request.context = {
            "title": default_title,
            "h2_tag": default_h2_tag,
        }

        args[0] = request
        args = tuple(args)

        output = func(*args, **kwargs)

        return output

    return wrapper
