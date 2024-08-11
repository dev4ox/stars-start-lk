from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseForbidden
from .models import BannedIP


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
        ip_address = request.META.get('REMOTE_ADDR')

        if BannedIP.objects.filter(ip_address=ip_address).exists():
            return HttpResponseForbidden("Your IP has been banned.")

        return self.get_response(request)
