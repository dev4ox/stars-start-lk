# pip lib
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

# my lib
from registration.models import CustomUser, Order, Services, Category
from .views_forms import AddOrGetDataSession


# manager
@login_required
def panels_manager_dashboard(request):
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

    return render(request, 'manager/dashboard.html', context)


# manager users
@login_required
def panels_manager_users(request):
    search_query = request.GET.get('search', '')

    # If there is a search query, we filter users by username or email
    if search_query:
        users_list = CustomUser.objects.filter(username__icontains=search_query).order_by('user_id')

    else:
        users_list = CustomUser.objects.all().order_by("user_id")

    orders = Order.objects.filter(manager=request.user.username)
    if len(orders) == 0:
        users_list = []

    else:
        orders = list(orders)
        users_list = list(users_list)
        count_users_list = 0

        for order in orders:
            while True:
                if order.user != users_list[count_users_list]:
                    del users_list[count_users_list]
                    count_users_list -= 1

                count_users_list += 1

                if count_users_list > len(users_list) - 1:
                    break

    paginator_user = Paginator(users_list, 5)  # 5 записей на страницу

    page_number = request.GET.get('page')
    page_obj_user = paginator_user.get_page(page_number)

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="user_manager_change",
        form_widgets_name={
            "password": "hidden_input"
        },
        url_redirect="panel_manager_users",
        model_name="custom_user",
        model_list_param_name=["user_id", ],
        html_vars={
            "title": "User details",
            "h2_tag": "User details",
        },
    )

    context = {
        "users_list": page_obj_user,
    }

    return render(request, 'manager/users.html', context)


# manager services
@login_required
def panels_manager_services(request):
    services_list = Services.objects.all().order_by('id')

    paginator = Paginator(services_list, 5)  # 5 записей на страницу

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    context = {
        "services_list": page_obj,
    }

    return render(request, 'manager/services.html', context)


# manager category
@login_required
def panels_manager_category(request):
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
    return render(request, 'manager/category.html', context)


# manager orders
@login_required
def panels_manager_orders(request):
    status = request.GET.get('status')

    if status == "all":
        orders_list = Order.objects.prefetch_related("service").all().order_by("order_id")

    elif status:
        orders_list = Order.objects.prefetch_related("service").filter(status=status).order_by("order_id")

    else:
        orders_list = Order.objects.prefetch_related("service").all().order_by("order_id")

    orders_list = list(orders_list)

    for order in orders_list:
        if order.manager != request.user.username:
            del orders_list[orders_list.index(order)]

    statuses = Order.STATUS_CHOICES

    request.session = AddOrGetDataSession(
        session=request.session,
        form_name="order_manager_change",
        url_redirect="panel_manager_orders",
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

    return render(request, 'manager/orders.html', context)
