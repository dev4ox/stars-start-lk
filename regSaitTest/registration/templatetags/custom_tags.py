from django import template

register = template.Library()


@register.filter
def get_by_index(list_, index):
    try:
        return list_[index]

    except:
        return None


@register.filter
def items(dict_):
    return dict_.items()
