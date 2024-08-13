from django.contrib import admin
from django import forms
from .models import CustomUser, Services, Category, Order, BannedIP, GroupServices
from .forms import ServicesChangeForm, OrderChangeForm, GroupServicesChangeForm
from .widgets import ReadOnlySelectMultiple
from .decorators.classes import CustomModelAdmin


class UserAdminForm(forms.ModelForm):

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'ip_address',
            "password",
            'first_name',
            'last_name',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if the user has access to edit groups
        if not self.current_user.has_perm('auth.change_group'):
            self.fields['groups'].widget = ReadOnlySelectMultiple()
        # Checking if the user has access to edit rights
        if not self.current_user.has_perm('auth.change_permission'):
            pass
            # self.fields['user_permissions'].widget = ReadOnlySelectMultiple()


class CategoryAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="registration", model_="category", route="admin_category")


class GroupServicesAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="registration", model_="groupservices", route="admin_service")

    form = GroupServicesChangeForm
    list_display = ('title', 'description')


class ServiceAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="registration", model_="services", route="admin_service")

    form = ServicesChangeForm


class OrderAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="registration", model_="order", route="admin_orders")

    form = OrderChangeForm


class CustomUserAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="auth", model_="user", route="admin_users")

    form = UserAdminForm
    list_display = ['username', 'ip_address', "password", 'first_name', 'last_name', 'is_staff']
    search_fields = ['username', 'ip_address', 'first_name', 'last_name']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    filter_horizontal = ['groups']

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     form.current_user = request.user
    #     return form


@admin.register(BannedIP)
class BannedIPAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="registration", model_="bannedip", route="admin_users")

    list_display = ('ip_address', 'description', 'created_at')
    search_fields = ('ip_address',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(GroupServices, GroupServicesAdmin)
admin.site.register(Services, ServiceAdmin)
admin.site.register(Order, OrderAdmin)
