import os
import uuid
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model, password_validation
from django.contrib.auth.views import PasswordResetConfirmView
from .forms import (
    CustomUserCreationForm,
    CustomUserChangeForm,
    CustomAuthenticationForm,
    PasswordResetRequestForm,
    OrderAddUser,
    CustomSetPasswordForm,
)
from .models import Order, Services, Category, BannedIP, CustomUser
from .utils import get_ip
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str, force_bytes
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _, activate as lang_activate
from django.contrib.admin.models import LogEntry
from django.core.paginator import Paginator
from .decorators.func import check_user_role
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from reportlab.lib.pagesizes import A6, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from tempfile import NamedTemporaryFile
from datetime import timedelta

# from django.core.handlers.wsgi import WSGIRequest

User = get_user_model()


def send_activation_email(user, request):
    mail_subject = _('Account Activation')
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = request.build_absolute_uri(f'/lk/activate/{uid}/{token}/')
    message = render_to_string('account_activation_email.html', {
        'user': user,
        'activation_url': activation_url,
    })
    send_mail(
        mail_subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.username],
        fail_silently=False,
        html_message=message,
    )


def set_language(request):
    if request.method == 'POST':
        user_language = request.POST.get('language')

        if user_language:
            lang_activate(user_language)
            response = redirect(request.META.get('HTTP_REFERER', '/'))
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, user_language)
            return response

    return redirect('/')


@login_required
def profile(request):
    last_order = Order.objects.filter(user=request.user).order_by('-date')[:1]

    if last_order:
        context = {
            "last_order": last_order[0],
        }

    else:
        context = {}

    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')

    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, "edit_profile.html", {"form": form, 'user': request.user})


# start admin block
@check_user_role
@login_required
def admin_dashboard(request):
    user_count = User.objects.count()

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

    return render(request, 'custom_admin/dashboard.html', context)


@check_user_role
@login_required
def admin_users(request):
    search_query = request.GET.get('search', '')
    banned_ip_list = BannedIP.objects.all().order_by("id")

    # If there is a search query, we filter users by username or email
    if search_query:
        users_list = User.objects.filter(username__icontains=search_query) | User.objects.filter(
            email__icontains=search_query).order_by('user_id')
    else:
        users_list = User.objects.all().order_by("user_id")

    paginator_user = Paginator(users_list, 5)  # 5 записей на страницу
    paginator_banned_ip = Paginator(banned_ip_list, 5)  # 5 записей на страницу

    page_number = request.GET.get('page')

    page_obj_user = paginator_user.get_page(page_number)
    page_obj_banned_ip = paginator_banned_ip.get_page(page_number)

    context = {
        "users_list": page_obj_user,
        "banned_ip_list": page_obj_banned_ip,
    }

    return render(request, 'custom_admin/users.html', context)


@check_user_role
@login_required
def admin_services(request):
    services_list = Services.objects.all().order_by('id')

    paginator = Paginator(services_list, 5)  # 5 записей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "services_list": page_obj,
    }
    return render(request, 'custom_admin/services.html', context)


@check_user_role
@login_required
def admin_category(request):
    sort_by = request.GET.get('sort_by', 'id')
    order = request.GET.get('order', 'asc')

    if sort_by == 'service.title':
        sort_by = 'service__title'

    if order == 'desc':
        sort_by = f'-{sort_by}'

    categories = Category.objects.all().order_by(sort_by)

    context = {
        'categories': categories,
        'current_sort': sort_by.lstrip('-'),
        'current_order': order,
    }
    return render(request, 'custom_admin/category.html', context)


@check_user_role
@login_required
def admin_orders(request):
    status = request.GET.get('status')

    if status == "all":
        orders_list = Order.objects.prefetch_related("service").all().order_by("order_id")

    elif status:
        orders_list = Order.objects.prefetch_related("service").filter(status=status).order_by("order_id")

    else:
        orders_list = Order.objects.prefetch_related("service").all().order_by("order_id")

    statuses = Order.STATUS_CHOICES

    context = {
        'orders_list': orders_list,
        'statuses': statuses,
        'current_status': status,
    }

    return render(request, 'custom_admin/orders.html', context)


@check_user_role
@login_required
def admin_reports(request):
    return render(request, 'custom_admin/reports.html')


# end admin block


@login_required
def orders(request):
    orders_list = Order.objects.prefetch_related("service").filter(user=request.user).order_by("order_id")
    paginator = Paginator(orders_list, 10)  # Показывать 10 заказов на странице

    page_number = request.GET.get('page')
    orders_list = paginator.get_page(page_number)

    context = {
        'orders': orders_list
    }
    return render(request, 'orders.html', context)


@login_required
def order_details(request, order_id):
    if request.user.is_superuser:
        return redirect(f"/admin/registration/order/{order_id}/change/")

    elif not request.user.is_superuser and request.user.is_active:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        context = {
            'order': order
        }

        return render(request, 'order_details.html', context)


@login_required
def order_pay(request):
    # order = get_object_or_404(Order, order_id=order_id, user=request.user)
    #
    # order.status = 'in_progress'
    # order.save()

    return render(request, "order_pay.html")


@login_required
def generate_or_get_pdf(request, order_id):
    # Получаем заказ пользователя
    order = get_object_or_404(Order, user=request.user, order_id=order_id)
    file_path = order.user_ticket_path

    if file_path is None or not os.path.exists(file_path):
        # Генерируем новый путь для сохранения файла
        file_path = os.path.join(settings.MEDIA_ROOT, f'order_user_tickets/ticket_starstart_{uuid.uuid4()}.pdf')

        # Зарегистрируем шрифт, поддерживающий кириллицу
        font_path = os.path.join(settings.BASE_DIR, 'fonts', 'DejaVuSans.ttf')
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

        # Создаем Canvas объект для генерации PDF файла с альбомной ориентацией
        p = canvas.Canvas(file_path, pagesize=landscape(A6))
        p.setFont("DejaVuSans", 12)
        width, height = landscape(A6)

        # Добавление логотипа в PDF
        logo_path = os.path.join(
            settings.STATICFILES_DIRS[0],
            'images/logo-stars-start-black-mini-300px.png'
        )  # путь к загруженному логотипу
        logo_width = 150
        logo_height = 65
        logo = ImageReader(logo_path)
        p.drawImage(logo, 20, height - logo_height - 20, width=logo_width, height=logo_height, mask='auto')

        # Добавление информации в PDF
        service_name = order.service.title  # Имя услуги
        category_name = order.category.name  # Имя категории
        order_number = order.order_id  # Номер заказа
        order_date = order.date.strftime('%Y-%m-%d %H:%M')  # Дата заказа

        # Настройка шрифтов и начальная позиция
        text_object = p.beginText(40, height - logo_height - 40)
        text_object.textLine(f"Имя услуги: {service_name}")
        text_object.textLine(f"Имя категории: {category_name}")
        text_object.textLine(f"Номер заказа: {order_number}")
        text_object.textLine(f"Дата заказа: {order_date}")
        p.drawText(text_object)

        # Генерация QR-кода
        relative_url = reverse("orders_details", kwargs={"order_id": order_id})
        qr_data = request.build_absolute_uri(relative_url)
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_image = qr.make_image(fill='black', back_color='white')

        # Сохранение QR-кода во временный файл
        with NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
            qr_image.save(temp_file, format='PNG')
            temp_file_path = temp_file.name

        # Вставка QR-кода в PDF в правом верхнем углу
        qr_size = 65

        # Позиция и размер QR-кода
        p.drawImage(temp_file_path, width - qr_size - 20, height - qr_size - 20, width=qr_size, height=qr_size)

        # Сохраняем файл
        p.save()

        # Удаляем временный файл
        os.remove(temp_file_path)

        # Обновляем путь к файлу в заказе и сохраняем заказ
        order.user_ticket_path = file_path
        order.save()

    # Открываем существующий или вновь созданный файл и возвращаем его в HTTP-ответе
    with open(file_path, 'rb') as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'

    return response


@login_required
def services(request):
    services_list = Services.objects.all().order_by("id")
    min_cost_categories_list = []

    for service in services_list:
        categories = Category.objects.filter(service=service).order_by('cost')[:1]

        if categories:
            min_cost_categories_list.append(categories[0].cost)

        else:
            min_cost_categories_list = []

    context = {
        "services_list": list(enumerate(services_list)),
        "min_cost_categories_list": min_cost_categories_list,
    }

    return render(request, 'services.html', context)


@login_required
def services_add_order(request, service_id):
    service = get_object_or_404(Services, id=service_id)
    category = Category.objects.prefetch_related("service").filter(service=service)

    if request.method == 'POST':
        form = OrderAddUser(request.POST)

        if form.is_valid():
            order = form.save(commit=False)

            order.user = request.user
            order.service = service
            order.status = 'new'  # Устанавливаем статус по умолчанию
            order.cost = order.category.cost

            order.save()
            return redirect('orders_pay')  # Перенаправление на страницу списка заказов

    else:
        initial_data = {
            "service": service,
            "status": "new",
        }

        form = OrderAddUser(initial=initial_data)

    # Получаем все комментарии модератора для отображения
    moder_comments = Order.objects.values_list('moder_comment', flat=True).distinct()

    context = {
        "service": service,
        "category": category,
        'form': form,
        'moder_comments': moder_comments,
    }

    return render(request, 'services_add_order.html', context)


@csrf_exempt
def load_categories(request):
    service_id = request.GET.get('service')
    categories = Category.objects.filter(service_id=service_id).order_by('name')

    return JsonResponse(
        {category.id: category.name for category in categories}
    )


@csrf_exempt
def get_category_cost(request):
    category_id = request.GET.get('category')

    try:
        category = Category.objects.get(id=category_id)
        return JsonResponse(
            {'cost': category.cost}
        )

    except Category.DoesNotExist:
        return JsonResponse(
            {'cost': 0}
        )


def registrations(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.ip_address = get_ip(request)
            user.save()

            send_activation_email(user, request)
            return redirect('message_about_activate')

        else:
            messages.error(request, _('Registration error. Please check the entered data.'))

    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {"form": form})


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'login.html'

    def form_valid(self, form):
        response = super().form_valid(form)

        user = get_object_or_404(CustomUser, username=form.cleaned_data.get("username"))
        user.ip_address = get_ip(self.request)
        user.save()

        return response


def password_reset_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetRequestForm(request.POST)

        if password_reset_form.is_valid():
            email = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(username=email)

            if associated_users.exists():
                for user in associated_users:
                    now = timezone.now()
                    # Проверка, был ли запрос на сброс пароля недавно
                    if user.last_password_reset_request and (now - user.last_password_reset_request) < timedelta(
                            minutes=settings.PASSWORD_RESET_TIMEOUT_MINUTES):
                        # Сообщение пользователю, что запрос был сделан недавно
                        messages.error(
                            request,
                            _("You can only request a password reset every {} minutes. Please try again later.".format(
                                settings.PASSWORD_RESET_TIMEOUT_MINUTES
                            )
                            )
                        )
                        return redirect("reset_password")

                    # Обновление метки времени последнего запроса
                    user.last_password_reset_request = now
                    user.save()

                    token = default_token_generator.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))

                    reset_link = request.build_absolute_uri(
                        reverse(
                            'password_reset_confirm', kwargs={
                                'uidb64': uid,
                                'token': token
                            }
                        )
                    )

                    expiry_time = timezone.now() + timedelta(hours=1)  # Ссылка будет действительна 1 час
                    context = {
                        'reset_link': reset_link,
                        'expiry_time': expiry_time,
                        'user': user
                    }

                    subject = _("Password Reset Requested")
                    email_template_name = "password_reset_email.html"
                    email_body = render_to_string(email_template_name, context)

                    send_mail(
                        subject,
                        email_body,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.username],
                        fail_silently=False,
                        html_message=email_body,
                    )

                # messages.success(request, _("Password reset link has been sent to your email."))
                return redirect("password_reset_done")

    password_reset_form = PasswordResetRequestForm()

    context = {
        "password_reset_form": password_reset_form
    }

    return render(request, "password_reset_request.html", context)


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["password_validators_help_text"] = password_validation.password_validators_help_texts()

        return context


def password_reset_done(request):
    return render(request, 'password_reset_done.html')


def message_about_activate(request):
    return render(request, 'message_about_activate.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, _('Your account has been successfully activated!'))
        return redirect('login')

    else:
        messages.error(request, _('Invalid activation link!'))
        return redirect('register')


@login_required
def payments(request):
    return render(request, 'payments.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def terms_of_service(request):
    return render(request, "terms_of_service.html")


def user_agreement(request):
    return render(request, "user_agreement.html")
