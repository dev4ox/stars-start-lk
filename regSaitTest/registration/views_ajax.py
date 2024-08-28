# python lib
from pathlib import Path
import os

# pip lib
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# my lib
from .models import Category, Services


@csrf_exempt
def get_category_cost(request):
    category_id = request.GET.get('category')
    # promo_code_value = request.GET.get('promo_code', None)

    try:
        category = Category.objects.get(id=category_id)
        cost = category.cost

        json_response = {
            'cost': cost,
        }

        return JsonResponse(json_response)

    except Category.DoesNotExist:
        return JsonResponse({'cost': 0})


def get_service_contents(request, service_id):
    service = get_object_or_404(Services, id=service_id)
    output_contents = []

    for path in service.contents:
        path = Path(path)

        file_obj = {
            "filename": path.name,
            "filepath": str(path.relative_to(settings.MEDIA_ROOT)),
        }

        output_contents.append(file_obj)

    json_response = {
        'contents': output_contents,
    }

    return JsonResponse(json_response)


@require_POST
def delete_service_content(request, service_id):
    filepath = request.GET.get('filepath')

    service = get_object_or_404(Services, id=service_id)

    if filepath and service:
        full_path = os.path.join(settings.MEDIA_ROOT, filepath)

        if os.path.exists(full_path):
            os.remove(full_path)

            service.contents = []
            service.save()

            return JsonResponse({'success': True})

    service.contents = []
    service.save()
    return JsonResponse({'success': False}, status=400)


# @require_GET
# def check_promo_code(request):
#     if not request.user.is_authenticated:
#         return JsonResponse({'error': 'User not authenticated'}, status=401)
#
#     promo_code = request.GET.get('promo_code', '')
#     user = request.user
#
#     # Параметры блокировки
#     block_duration = timedelta(hours=1)
#
#     if user.is_promo_blocked(block_duration):
#         remaining_time = (block_duration - (timezone.now() - user.last_promo_attempt)).total_seconds() // 60
#
#         return JsonResponse({
#             'error': f'Превышено количество попыток. Попробуйте снова через {int(remaining_time)} минут.'
#         })
#
#     try:
#         promo = PromoCode.objects.get(value=promo_code, is_active=True)
#
#         if promo.is_valid(request.user):
#             user.reset_promo_attempts()  # Сброс попыток при успешной проверке
#
#             return JsonResponse({
#                 'is_valid': True,
#                 'discount': promo.discount
#             })
#
#         else:
#             user.increment_promo_attempts()
#             return JsonResponse({
#                 'is_valid': False,
#                 'error': 'Промо-код не активен или истек срок действия.'
#             })
#
#     except PromoCode.DoesNotExist:
#         user.increment_promo_attempts()
#         return JsonResponse({'is_valid': False, 'error': 'Неверный промо-код.'})
