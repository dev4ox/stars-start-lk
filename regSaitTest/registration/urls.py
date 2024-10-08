from django.urls import path
from . import views, views_ajax
from django.contrib.auth import views as auth_views

urlpatterns = [
    # user
    path('', views.profile, name='profile'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.registrations, name='register'),
    path('message_about_activate/', views.message_about_activate, name='message_about_activate'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('logout/', views.logout_view, name='logout'),

    # services
    path('services/', views.services, name="services"),
    path('services/<int:service_id>/add_order/', views.services_add_order, name="services_add_order"),
    path("services/message_negotiated_price/", views.services_message_zero_cost,
         name="services_message_negotiated_price"),

    # orders
    path('orders/', views.orders, name='orders'),
    path('orders/<int:order_id>/get_ticket/', views.generate_or_get_pdf, name='order_get_tickets'),
    path('orders/<int:service_id>/view_content/', views.order_service_content, name='order_view_content'),
    path('orders/<int:order_id>/orders_details', views.order_details, name='orders_details'),
    path('orders/<int:order_id>/pay/', views.order_pay, name='orders_pay'),

    # payments
    path('payments/', views.payments, name='payments'),

    # password change
    path("password_change/", auth_views.PasswordChangeView.as_view(template_name="password_change.html"),
         name="password_change"),
    path("password_change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="password_change_done.html"),
         name="password_change_done"),

    # reset password
    path('reset_password/', views.password_reset_request, name="reset_password"),
    path(
        'reset/<uidb64>/<token>/',
        views.CustomPasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ), name='password_reset_confirm'
    ),
    path('reset_password/done/', auth_views.PasswordResetDoneView.as_view(template_name="password_reset_done.html"),
         name="password_reset_done"),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),
         name='password_reset_complete'),

    # activate account
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    # other
    path('set-language/', views.set_language, name='set_language'),
    path("terms_of_service/", views.terms_of_service, name="terms_of_service"),
    path("user_agreement/", views.user_agreement, name="user_agreement"),
]

urlpatterns_ajax = [
    # ajax
    # path('ajax/load-categories/', views.load_categories, name='load_categories'),
    # path('ajax/check-promo-code/', views_ajax.check_promo_code, name='check_promo_code'),
    path('ajax/get-category-cost/', views_ajax.get_category_cost, name='get_category_cost'),
    path('ajax/get-service-contents/<int:service_id>/', views_ajax.get_service_contents, name='get_service_contents'),
    path(
        'ajax/delete-service-content/<int:service_id>/',
        views_ajax.delete_service_content,
        name='delete_service_content'
    ),
]
