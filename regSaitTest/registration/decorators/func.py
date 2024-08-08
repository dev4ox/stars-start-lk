from functools import wraps
from typing import Callable
from django.http import HttpResponseRedirect
from django.urls import reverse


def check_user_role(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        user = request.user

        if user.is_staff:
            output = func(*args, **kwargs)

            return output

        else:
            return HttpResponseRedirect(reverse("profile"))

    return wrapper
