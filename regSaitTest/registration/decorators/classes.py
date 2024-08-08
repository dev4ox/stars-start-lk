from django.contrib import admin
from django.urls import reverse
from django.http import HttpResponseRedirect


class CustomModelAdmin(admin.ModelAdmin):
    def __init__(self, model, admin_site, app: str, model_: str, route: str):
        super().__init__(model, admin_site)
        self.app = app
        self.model_ = model_
        self.route = route

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    # def get_queryset(self, request):
    #     qs = super().get_queryset(request)
    #     # Show an empty list if the user does not have special permission
    #     if not request.user.has_perm(f'{self.app}.view_{self.model_}_list'):
    #         return qs.none()
    #     return qs

    def get_actions(self, request):
        actions = super().get_actions(request)
        # Remove actions if the user does not have special permission
        if not request.user.has_perm(f'{self.app}.view_{self.model_}_list'):
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def changelist_view(self, request, extra_context=None):
        if not request.user.has_perm(f'{self.app}.view_{self.model_}_list'):
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(reverse("admin_dashboard"))

        return super().changelist_view(request, extra_context)

    def response_change(self, request, obj):
        if "_addanother" in request.POST:
            # Redirect to custom route after saving and adding another object
            return HttpResponseRedirect(reverse(self.route))
        elif "_save" in request.POST:
            # Redirect to custom route after simple save
            return HttpResponseRedirect(reverse(self.route))

        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if "_addanother" in request.POST:
            # Redirect to custom route after saving and adding another object
            return HttpResponseRedirect(reverse(self.route))
        elif "_save" in request.POST:
            # Redirect to custom route after simple save
            return HttpResponseRedirect(reverse(self.route))

        return super().response_add(request, obj, post_url_continue)

    def response_delete(self, request, obj_display, obj_id):
        # Redirect to custom route after deletion
        return HttpResponseRedirect(reverse(self.route))
