from django import template

register = template.Library()

@register.filter
def abs_value(value):
    """Negatif değeri pozitif yapar"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

