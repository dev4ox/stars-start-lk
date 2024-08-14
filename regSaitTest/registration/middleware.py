from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import BannedIP
from .utils import get_ip


class AdminCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(reverse('admin:index')):
            if not request.user.is_authenticated:
                return redirect('login')
            # Add your additional verification here
            # if not request.user.is_superuser:
            #     return redirect('profile')

            if not request.user.is_staff:
                return redirect("profile")

        response = self.get_response(request)
        return response


class BanIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip_address = get_ip(request)

        if BannedIP.objects.filter(ip_address=ip_address).exists():
            message = format_html(
                _('Your IP has been banned. For more information, visit {link_start}this page{link_end}.'),
                link_start='<a href="https://t.me/starstartmanager">',
                link_end='</a>'
            )
            return HttpResponseForbidden(message)

        return self.get_response(request)
