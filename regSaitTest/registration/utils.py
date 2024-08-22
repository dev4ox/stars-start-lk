# python lib
from typing import Union

# pip lib
from django.db.models import Case, When
from django.db.models.query import QuerySet

# my lib
from .models import Category, Services


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
