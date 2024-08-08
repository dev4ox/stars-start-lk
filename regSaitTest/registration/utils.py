from django.conf import settings
from django.urls import reverse


def build_absolute_url(viewname, kwargs=None):
    relative_url = reverse(viewname, kwargs=kwargs)
    absolute_url = f"{settings.MY_SITE_PROTOCOL}://{settings.MY_SITE_DOMAIN}{relative_url}"
    return absolute_url
