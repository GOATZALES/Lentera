import re
from django import template

register = template.Library()

@register.filter

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def safe_slugify(value):
    value = value.lower()
    value = re.sub(r'\s+', '_', value)  # ganti spasi dengan _
    value = re.sub(r'[^a-z0-9_]', '', value)  # hilangkan karakter tidak valid
    return value

@register.filter
def splitlines(value):
    return value.splitlines()