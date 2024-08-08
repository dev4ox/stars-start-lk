from django.contrib import admin
from django import forms
from .models import CustomUser, Services, Category, Order
from .forms import ServicesChangeForm, OrderChangeForm
from .widgets import ReadOnlySelectMultiple
from .decorators.classes import CustomModelAdmin
from decimal import Decimal


class UserAdminForm(forms.ModelForm):

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
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


class ServiceAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="registration", model_="services", route="admin_service")

    form = ServicesChangeForm

    # def formfield_for_manytomany(self, db_field, request, **kwargs):
    #     form_field = super().formfield_for_manytomany(db_field, request, **kwargs)
    #     if db_field.name == 'category':
    #         if 'id' not in form_field.widget.attrs:
    #             form_field.widget.attrs['id'] = db_field.name
    #
    #         # Получаем связанные объекты и значения поля cost
    #         related_model = db_field.related_model
    #         related_objects = related_model.objects.all()
    #         options = []
    #         for obj in related_objects:
    #             if hasattr(obj, 'cost'):
    #                 cost = obj.cost
    #                 if isinstance(cost, Decimal):
    #                     cost = float(cost)  # Преобразуем Decimal в float
    #                 options.append((obj.pk, f"{obj} (Стоимость: {cost})"))
    #
    #         # Генерируем HTML для выбора с измененными текстами опций
    #         form_field.choices = options
    #
    #     return form_field


class OrderAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="registration", model_="order", route="admin_orders")

    form = OrderChangeForm


class CustomUserAdmin(CustomModelAdmin):
    def __init__(self, model, admin_site):
        super().__init__(model, admin_site, app="auth", model_="user", route="admin_users")

    form = UserAdminForm
    list_display = ['username', 'email', "password", 'first_name', 'last_name', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    filter_horizontal = ['groups']

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     form.current_user = request.user
    #     return form


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Services, ServiceAdmin)
admin.site.register(Order, OrderAdmin)
