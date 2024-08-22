# pip lib
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

# my lib
from .models import Category, PromoCode
from .utils import check_date_promo_code


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


@require_GET
def check_promo_code(request):
    promo_code_value = request.GET.get('promo_code', '')

    response = {}

    try:
        promo_code = PromoCode.objects.get(value=promo_code_value, is_active=True)

        if check_date_promo_code(promo_code):
            response = {
                'is_valid': True,
                'discount': promo_code.discount
            }

            return JsonResponse(response)

        else:
            response = {
                'is_valid': False
            }

            return JsonResponse(response)

    except PromoCode.DoesNotExist:
        response = {
            'is_valid': False
        }

        return JsonResponse(response)
