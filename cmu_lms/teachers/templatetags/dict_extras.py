from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allow dictionary lookups by key in templates."""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def dict_key(d, key):
    return d.get(key) if isinstance(d, dict) else None
