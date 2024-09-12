# pip lib
from django.db import transaction

# my lib
from .models import GroupServices
from registration.models import Services


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
