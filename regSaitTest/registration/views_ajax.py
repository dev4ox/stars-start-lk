# python lib
from datetime import timedelta

# pip lib
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

# my lib
from .models import Category, PromoCode


@csrf_exempt
def get_category_cost(request):
    category_id = request.GET.get('category')
    promo_code_value = request.GET.get('promo_code', None)

    try:
        category = Category.objects.get(id=category_id)
        cost = category.cost

        discount = None

        if promo_code_value:

            try:
                promo_code = PromoCode.objects.get(value=promo_code_value)

                if promo_code.is_active and promo_code.expiration_date >= timezone.now().date():
                    discount = promo_code.discount

            except PromoCode.DoesNotExist:
                pass

        json_response = {
            'cost': cost,
            'discount': discount
        }

        return JsonResponse(json_response)

    except Category.DoesNotExist:
        return JsonResponse({'cost': 0, 'discount': None})


@require_GET
def check_promo_code(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)

    promo_code = request.GET.get('promo_code', '')
    user = request.user

    # Параметры блокировки
    block_duration = timedelta(hours=1)

    if user.is_promo_blocked(block_duration):
        remaining_time = (block_duration - (timezone.now() - user.last_promo_attempt)).total_seconds() // 60
        return JsonResponse({
            'error': f'Превышено количество попыток. Попробуйте снова через {int(remaining_time)} минут.'
        })

    try:
        promo = PromoCode.objects.get(value=promo_code, is_active=True)

        if promo.is_valid():
            user.reset_promo_attempts()  # Сброс попыток при успешной проверке
            return JsonResponse({
                'is_valid': True,
                'discount': promo.discount
            })

        else:
            user.increment_promo_attempts()
            return JsonResponse({
                'is_valid': False,
                'error': 'Промо-код не активен или истек срок действия.'
            })

    except PromoCode.DoesNotExist:
        user.increment_promo_attempts()
        return JsonResponse({'is_valid': False, 'error': 'Неверный промо-код.'})
