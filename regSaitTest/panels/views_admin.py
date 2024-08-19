# pip lib
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.models import LogEntry
from django.core.paginator import Paginator

# my lib
from registration.models import CustomUser, Order, Services, Category
from .models import BannedIP, GroupServices
from .views_forms import AddOrGetDataSession


# admin dashboard
@login_required
def panels_admin_dashboard(request):
    user_count = CustomUser.objects.count()

    new_order_count = Order.objects.filter(status="new").count()
    in_progress_order_count = Order.objects.filter(status="in_progress").count()
    active_order_count = new_order_count + in_progress_order_count

    # Get the last 10 actions
    recent_actions = LogEntry.objects.all().select_related('content_type', 'user').order_by('-action_time')[:4]

    context = {
        "user_count": user_count,
        "active_order_count": active_order_count,
        "recent_actions": recent_actions,
    }

    return render(request, 'admin/dashboard.html', context)


# admin users
@login_required
def panels_admin_users(request):
    search_query = request.GET.get('search', '')

    # If there is a search query, we filter users by username or email
    if search_query:
        users_list = CustomUser.objects.filter(username__icontains=search_query) | CustomUser.objects.filter(
            email__icontains=search_query).order_by('user_id')
    else:
        users_list = CustomUser.objects.all().order_by("user_id")

    paginator_user = Paginator(users_list, 5)  # 5 записей на страницу

    page_number = request.GET.get('page')
    page_obj_user = paginator_user.get_page(page_number)

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="user_admin_change",
        form_widgets_name={
            "password": "hidden_input"
        },
        url_redirect="panel_admin_users",
        model_name="custom_user",
        model_list_param_name=["user_id", ],
        html_vars={
            "title": "User change",
            "h2_tag": "User change",
        },
    )

    context = {
        "users_list": page_obj_user,
    }

    return render(request, 'admin/users.html', context)


# admin banned ip
@login_required
def panels_admin_banned_ip(request):
    banned_ip_list = BannedIP.objects.all().order_by("id")

    paginator_banned_ip = Paginator(banned_ip_list, 5)

    page_number = request.GET.get('page')

    page_obj_banned_ip = paginator_banned_ip.get_page(page_number)

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="banned_ip_change",
        url_redirect="panel_admin_banned_ips",
        model_name="banned_ip",
        model_list_param_name=["id", ],
        html_vars={
            "title": "Banned IP change",
            "h2_tag": "Banned IP change",
        },
    )

    context = {
        "banned_ip_list": page_obj_banned_ip,
    }

    return render(request, 'admin/banned_ip.html', context)


# admin group service
@login_required
def panels_admin_group_service(request):
    group_service = GroupServices.objects.all().order_by("id")

    paginator_group_service = Paginator(group_service, 5)

    page_number = request.GET.get('page')

    page_obj_group_service = paginator_group_service.get_page(page_number)

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="group_service_change",
        url_redirect="panel_admin_group_service",
        model_name="group_service",
        model_list_param_name=["id", ],
        html_vars={
            "title": "Group service change",
            "h2_tag": "Group service change",
        },
    )

    context = {
        "group_service": page_obj_group_service,
    }

    return render(request, "admin/group_service.html", context)


# admin services
@login_required
def panels_admin_services(request):
    services_list = Services.objects.all().order_by('id')

    paginator = Paginator(services_list, 5)  # 5 записей на страницу

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="service_change",
        url_redirect="panel_admin_service",
        model_name="services",
        model_list_param_name=["id", ],
        html_vars={
            "title": "Service change",
            "h2_tag": "Service change",
        },
    )

    context = {
        "services_list": page_obj,
    }

    return render(request, 'admin/services.html', context)


# admin category
@login_required
def panels_admin_category(request):
    sort_by = request.GET.get('sort_by', 'id')
    order = request.GET.get('order', 'asc')

    if sort_by == 'service.title':
        sort_by = 'service__title'

    if order == 'desc':
        sort_by = f'-{sort_by}'

    categories = Category.objects.all().order_by(sort_by)

    paginator = Paginator(categories, 5)  # 5 записей на страницу

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="category_change",
        url_redirect="panel_admin_category",
        model_name="category",
        model_list_param_name=["id", ],
        html_vars={
            "title": "Category change",
            "h2_tag": "Category change",
        },
    )

    context = {
        'categories': page_obj,
        'current_sort': sort_by.lstrip('-'),
        'current_order': order,
    }
    return render(request, 'admin/category.html', context)


# admin orders
@login_required
def panels_admin_orders(request):
    status = request.GET.get('status')

    if status == "all":
        orders_list = Order.objects.prefetch_related("service").all().order_by("order_id")

    elif status:
        orders_list = Order.objects.prefetch_related("service").filter(status=status).order_by("order_id")

    else:
        orders_list = Order.objects.prefetch_related("service").all().order_by("order_id")

    statuses = Order.STATUS_CHOICES

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="order_change",
        url_redirect="panel_admin_orders",
        model_name="order",
        model_list_param_name=["order_id", ],
        model_save_commit=False,
        model_link_field_value={
            "cost": "category.cost"
        },
        html_vars={
            "title": "Order change",
            "h2_tag": "Order change",
        },
    )

    context = {
        'orders_list': orders_list,
        'statuses': statuses,
        'current_status': status,
    }

    return render(request, 'admin/orders.html', context)


# admin reports
@login_required
def panels_admin_reports(request):
    return render(request, 'admin/reports.html')
