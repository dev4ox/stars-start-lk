from django.shortcuts import redirect
from django.urls import reverse


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
