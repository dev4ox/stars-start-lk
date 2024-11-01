# python lib
import os
import uuid
import qrcode
from tempfile import NamedTemporaryFile
from datetime import timedelta
from pathlib import Path

# pip lib
from reportlab.lib.pagesizes import A6, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from yookassa import Configuration, Payment

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, get_user_model, password_validation
from django.contrib.auth.views import PasswordResetConfirmView
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str, force_bytes
from django.utils.translation import gettext_lazy as _, activate as lang_activate
from django.core.mail import send_mail
from django.core.paginator import Paginator
# from django.core.handlers.wsgi import WSGIRequest
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse

# my lib
from .forms import (
    CustomUserCreationForm,
    CustomUserChangeForm,
    CustomAuthenticationForm,
    PasswordResetRequestForm,
    OrderAddUser,
    CustomSetPasswordForm,
)
from .models import Order, Services, CustomUser, PromoCode, GroupServices
from .utils import get_min_cost, get_ip
from .tasks import check_payment_status

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
    last_order = Order.objects.filter(user=request.user).order_by('-order_id')[:1]

    if last_order:
        context = {
            "last_order": last_order[0],
        }
        print(last_order)


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
        pass
        # request.session = AddOrGetDataSession(
        #     session=request.session,
        #     form_name="order_change",
        #     url_redirect="orders",
        #     model_name="order",
        #     model_list_param_name=["order_id", ],
        #     model_save_commit=False,
        #     model_link_field_value={
        #         "cost": "category.cost"
        #     },
        #     html_vars={
        #         "title": "Order change",
        #         "h2_tag": "Order change",
        #     },
        # )

        return redirect("panel_form_edit", order_id)


@login_required
def order_service_content(request, service_id):
    service = Services.objects.get(id=service_id)  # Получаем объект Services (замените на нужный)
    files = service.contents  # Предполагается, что это список путей к файлам

    file_data = []

    for file_path in files:
        file_path = Path(file_path)
        url = os.path.join(settings.MEDIA_URL, "service_contents", str(service.id), file_path.name)

        if file_path.suffix in ['.docx', '.pdf', '.mp3', '.mp4', '.jpg', '.rar', '.zip']:
            file_data.append(
                {
                    'name': file_path.name,
                    'url': url,
                    'type': file_path.suffix,
                }
            )

    context = {
        "service": service,
        'files': file_data,
    }

    return render(request, 'order_service_contents_view.html', context)


@login_required
def order_pay(request, order_id):
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
    group_services = GroupServices.objects.all().order_by("id")
    search_query = request.GET.get('search', '')

    if search_query:
        services_list = Services.objects.filter(title__icontains=search_query) | Services.objects.filter(
            description__icontains=search_query).order_by('id')
    else:
        services_list = Services.objects.all().order_by("id")

    group_services = list(group_services)
    services_list = list(services_list)
    dict_groups = {}

    for group in group_services:
        if group.is_active:
            dict_groups[group] = []

        for service in services_list:
            if service.group_services == group and service.is_active and group.is_active:
                dict_groups[group].append(service)

        if group.is_active and not dict_groups[group]:
            del dict_groups[group]

    # # Список для хранения индексов групп, которые нужно удалить
    # groups_to_delete = []
    #
    # # Проверяем каждую группу услуг
    # for group in group_services:
    #     # Получаем все услуги, связанные с этой группой
    #     services_in_group = [service for service in services_list if service.group_services == group]
    #
    #     # Если в группе нет активных услуг, удаляем эту группу
    #     if not services_in_group:
    #         groups_to_delete.append(group)
    #
    # # Удаляем неактивные группы
    # for group in groups_to_delete:
    #     group_services.remove(group)

    # Обновляем минимальные цены для оставшихся услуг
    for group, services in dict_groups.items():
        for service in services:
            service.min_cost = get_min_cost(service, output_int_num=True)

    context = {
        # "services_list": list(enumerate(services_list)),
        # "group_services": group_services,
        "dict_groups": dict_groups,
        "search_query": search_query,
    }

    return render(request, 'services.html', context)


@login_required
def services_add_order(request, service_id):
    service = get_object_or_404(Services, id=service_id)

    initial_data = {
        "service": service,
        "status": "new",
        "user": request.user
    }

    if request.method == 'POST':
        form = OrderAddUser(request.POST, initial=initial_data)

        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.service = service

            promo_code_value = form.cleaned_data.get("promo_code", "").strip()
            if promo_code_value:
                try:
                    promo_code = PromoCode.objects.get(value=promo_code_value)

                    if promo_code.is_valid(request.user, service, order.category):
                        cost_with_discount = promo_code.apply_discount(int(order.category.cost))

                        order.cost = cost_with_discount
                        order.discount = promo_code.discount
                        promo_code.use(request.user)

                    else:
                        order.cost = order.category.cost

                except PromoCode.DoesNotExist:
                    order.cost = order.category.cost

            else:
                order.cost = order.category.cost

            order.status = 'new'
            order.save()

            if order.cost != 0:
                return redirect('orders')

            else:
                return redirect("services_message_negotiated_price")

    else:
        form = OrderAddUser(initial=initial_data)

    # Получаем все комментарии модератора для отображения
    moder_comments = Order.objects.values_list('moder_comment', flat=True).distinct()

    context = {
        "service": service,
        'form': form,
        'moder_comments': moder_comments,
    }

    return render(request, 'services_add_order.html', context)


def services_message_zero_cost(request):
    return render(request, "message_add_services_with_zero_cost.html")


# @csrf_exempt
# def load_categories(request):
#     service_id = request.GET.get('service')
#     categories = Category.objects.filter(service_id=service_id).order_by('cost')
#     print(categories)
#
#     json_response = {}
#
#     for category in categories:
#         if category.is_active:
#             json_response[category.id] = category.name
#
#     print(json_response)
#
#     return JsonResponse(
#         json_response
#     )


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
