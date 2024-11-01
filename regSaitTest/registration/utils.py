# python lib
from typing import Union

# pip lib
from django.db import transaction
from django.db.models import Case, When
from django.db.models.query import QuerySet

# my lib
from .models import Category, Services, GroupServices


def convert_list_to_queryset(
        list_: list,
        order_by: Union[str | None] = None,
        list_original: bool = False
) -> QuerySet:
    # Преобразуем список обратно в QuerySet
    pks = [model_field.pk for model_field in list_]

    if list_original:
        preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(pks)])

        return Category.objects.filter(pk__in=pks).order_by(preserved_order)

    if order_by is not None:
        return Category.objects.filter(pk__in=pks).order_by(order_by)

    else:
        return Category.objects.filter(pk__in=pks)


def get_min_cost(
        service: Services,
        output_int_num: bool = False,
        output_queryset: bool = False
) -> Union[int | QuerySet]:
    categories = Category.objects.filter(service=service).order_by('cost')
    categories = list(categories)

    category_with_cost_zero = None

    for category in categories:
        if not category.is_active:
            del categories[categories.index(category)]

    for category in categories:
        if int(category.cost) == 0:
            category_with_cost_zero = categories.index(category)

    if category_with_cost_zero is not None:
        if len(categories) - 1 != category_with_cost_zero:
            min_cost_obj = categories[category_with_cost_zero + 1]

        else:
            min_cost_obj = categories[category_with_cost_zero]

        if output_int_num:
            return int(min_cost_obj.cost)

        elif output_queryset:
            if len(categories) - 1 != category_with_cost_zero:
                del categories[category_with_cost_zero + 1]

                categories.insert(0, min_cost_obj)

                return convert_list_to_queryset(categories, list_original=True)

            else:
                return convert_list_to_queryset(categories)

    elif categories:
        if output_int_num:
            return int(categories[0].cost)

        elif output_queryset:
            return convert_list_to_queryset(categories, order_by="cost")


def get_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # Реальный IP клиента

    else:
        ip = request.META.get('REMOTE_ADDR')  # IP без использования прокси

    return ip


def update_group_service_id(group_service, old_id: int, new_id: int) -> None:
    with transaction.atomic():
        # Шаг 1: Изменение ID в таблице GroupServices
        group_service.id = new_id
        group_service.save()

        # Шаг 2: Обновление связанных записей в таблице Services
        Services.objects.filter(group_services_id=old_id).update(group_services_id=new_id)

        group_service = GroupServices.objects.get(id=old_id)
        group_service.delete()

