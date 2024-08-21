import decimal
import os
import uuid
import qrcode
from reportlab.lib.pagesizes import A6, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from tempfile import NamedTemporaryFile
from datetime import timedelta
from yookassa import Configuration, Payment

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
from .models import Order, Services, Category, CustomUser
from panels.models import GroupServices
from panels.utils import get_ip
from panels.tasks import check_payment_status
from panels.views_forms import AddOrGetDataSession

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str, force_bytes
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext_lazy as _, activate as lang_activate
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
# from django.core.handlers.wsgi import WSGIRequest

User = get_user_model()


def send_activation_email(user, request):
    mail_subject = _('Account Activation')
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = request.build_absolute_uri(f'/lk/activate/{uid}/{token}/')
    message = render_to_string(
        'account_activation_email.html',
        {
            'user': user,
            'activation_url': activation_url,
        }
    )

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
    if request.user.role == 0:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        context = {
            'order': order,
            "user": order.user,
        }

        return render(request, 'order_details.html', context)

    elif request.user.role == 3 or request.user.role == 1:
        order = get_object_or_404(Order, order_id=order_id)

        context = {
            'order': order,
            "user": order.user,
        }

        return render(request, "observer/order_user_details.html", context)

    elif request.user.role == -1 or request.user.role == 2:
        request.session = AddOrGetDataSession(
            session=request.session,
            form_name="order_change",
            url_redirect="orders",
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

        return redirect("panel_form_edit", order_id)


@login_required
def order_pay(request, order_id):
    # return render(request, "order_pay.html")
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    Configuration.account_id = settings.YOKASSA_ACCOUNT_ID
    Configuration.secret_key = settings.YOKASSA_SECRET_KEY

    receipt = {
        "customer": {
            "full_name": f"{request.user.first_name} {request.user.last_name}",
            "email": request.user.username,
            "phone": str(request.user.phone_number)
        },
        "items": [
            {
                "description": f"Заказ №{order.order_id}",
                "quantity": "1.00",
                "amount": {
                    "value": str(order.cost),
                    "currency": "RUB"
                },
                "vat_code": 4,  # Убедитесь, что код НДС соответствует вашему случаю
                "payment_mode": "full_payment",
                "payment_subject": "commodity"
            }
        ]
    }

    payment_value = {
        "amount": {
            "value": order.cost,
            "currency": "RUB"
        },

        "confirmation": {
            "type": "redirect",
            "return_url": settings.YOKASSA_RETURN_URL
        },

        "capture": True,
        "description": f"Заказ №{order.order_id}",

        "metadata": {
          "order_id": f"{order.order_id}"
        },
        "receipt": receipt
    }

    trans_id = uuid.uuid4()
    payment = Payment.create(payment_value, trans_id)
    # print(trans_id, payment_to_yokassa.id)

    check_payment_status.delay(payment.id, order.order_id)

    # return JsonResponse(payment.json(), safe=False)
    return redirect(payment.confirmation["confirmation_url"])


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


def services(request):
    services_list = Services.objects.all().order_by("id")
    # group_services = GroupServices.objects.all().order_by("title")
    min_cost_categories_list = []
    search_query = request.GET.get('search', '')

    if search_query:
        group_services = GroupServices.objects.filter(title__icontains=search_query) | GroupServices.objects.filter(
            description__icontains=search_query).order_by('id')

    else:
        group_services = GroupServices.objects.all().order_by("id")

    group_services = list(group_services)
    services_list = list(services_list)

    for index, group in enumerate(group_services):
        if not group.is_active:
            del group_services[group_services.index(group)]

        if not services_list[index].is_active:
            services_group_list = Services.objects.filter(group_services=group)
            count_deactivate = 0

            for service_group in services_group_list:
                if not service_group.is_active:
                    count_deactivate += 1

            if count_deactivate == len(services_group_list):
                del group_services[index]

            del services_list[index]

    for service in services_list:
        categories = Category.objects.filter(service=service).order_by('cost')

        if categories:
            for category in categories:
                if category.cost != 0:
                    min_cost_categories_list.append(int(category.cost))
                    break

                # elif category.cost == 0:
                #     min_cost_categories_list.append(0)
                #     break

    context = {
        "services_list": list(enumerate(services_list)),
        "group_services": group_services,
        "min_cost_categories_list": min_cost_categories_list,
        "search_query": search_query,
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
            return redirect('orders')  # Перенаправление на страницу списка заказов

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
    categories = Category.objects.filter(service_id=service_id).order_by('cost')
    print(categories)

    json_response = {}

    for category in categories:
        if category.is_active:
            json_response[category.id] = category.name

    return JsonResponse(
        json_response
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
                        [user.username],  # Используем user.username, так как это email
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
