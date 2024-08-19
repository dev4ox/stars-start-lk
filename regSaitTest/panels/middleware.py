from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import BannedIP
from .utils import get_ip


class CheckRoleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        """
        -1 == admin
        0 == user
        1 == manager
        2 == moderator
        3 == observer
        """

    def __call__(self, request):
        if not request.user.is_anonymous:
            if request.path.startswith(reverse('panel_admin_dashboard')):
                if request.user.role == 0 or request.user.role == 3:
                    return redirect('profile')

                elif request.user.role == 1:
                    return redirect("panel_manager_dashboard")

                elif request.user.role == 2:
                    return redirect("panel_moderator_dashboard")

            elif request.path.startswith(reverse('panel_moderator_dashboard')):
                if request.user.role == 0 or request.user.role == 3:
                    return redirect('profile')

                elif request.user.role == 1:
                    return redirect("panel_manager_dashboard")

            elif request.path.startswith(reverse('panel_manager_dashboard')):
                if request.user.role == 0 or request.user.role == 3:
                    return redirect('profile')

        response = self.get_response(request)
        return response


class BanIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = get_ip(request)

        if BannedIP.objects.filter(ip_address=ip_address).exists():
            message = format_html(
                _('Your IP has been banned. For more information, visit:')
                + ' <a href="https://t.me/starstartmanager">t.me/starstartmanager</a>',
            )
            return HttpResponseForbidden(message)

        return self.get_response(request)
