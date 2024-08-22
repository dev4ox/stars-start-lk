from django.urls import path
from . import views_forms, views_admin, views_manager, views_moderator

urlpatterns = [
    # forms
    path("form/<int:id_>/add/", views_forms.panels_form_change, name="panel_form_add"),
    path("form/<int:id_>/edit/", views_forms.panels_form_change, name="panel_form_edit"),
    path("form/<int:id_>/delete/", views_forms.panels_form_delete, name="panel_form_delete"),
    path("form/<int:id_>/details/", views_forms.panels_form_details, name="panel_form_details"),

    # admin
    path("admin/", views_admin.panels_admin_dashboard, name="panel_admin_dashboard"),

    # admin users
    path("admin/users/", views_admin.panels_admin_users, name="panel_admin_users"),

    # admin banned ip
    path("admin/banned_ip/", views_admin.panels_admin_banned_ip, name="panel_admin_banned_ips"),

    # admin promo codes
    path("admin/promo_codes", views_admin.panels_admin_promo_codes, name="panel_admin_promo_codes"),

    # admin group service
    path("admin/group_service/", views_admin.panels_admin_group_service, name="panel_admin_group_service"),

    # admin service
    path("admin/service/", views_admin.panels_admin_services, name="panel_admin_service"),

    # admin category
    path("admin/category/", views_admin.panels_admin_category, name="panel_admin_category"),

    # admin orders
    path("admin/orders/", views_admin.panels_admin_orders, name="panel_admin_orders"),

    # admin reports
    path("admin/reports/", views_admin.panels_admin_reports, name="panel_admin_reports"),

    # manager
    path("manager/", views_manager.panels_manager_dashboard, name="panel_manager_dashboard"),

    # manager users
    path("manager/users/", views_manager.panels_manager_users, name="panel_manager_users"),

    # manager service
    path("manager/service/", views_manager.panels_manager_services, name="panel_manager_service"),

    # manager category
    path("manager/category/", views_manager.panels_manager_category, name="panel_manager_category"),

    # manager orders
    path("manager/orders/", views_manager.panels_manager_orders, name="panel_manager_orders"),

    # moderator
    path("moderator/", views_moderator.panels_moderator_dashboard, name="panel_moderator_dashboard"),

    # moderator users
    path("moderator/users/", views_moderator.panels_moderator_users, name="panel_moderator_users"),

    # moderator group service
    path("moderator/group_service/", views_moderator.panels_moderator_group_service,
         name="panel_moderator_group_service"),

    # moderator service
    path("moderator/service/", views_moderator.panels_moderator_services, name="panel_moderator_service"),

    # moderator category
    path("moderator/category/", views_moderator.panels_moderator_category, name="panel_moderator_category"),

    # moderator orders
    path("moderator/orders/", views_moderator.panels_moderator_orders, name="panel_moderator_orders"),
]
