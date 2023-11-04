from django import template

register = template.Library()

@register.filter
def convert_to_myr(price_usd):
    conversion_rate = 4
    price_myr = price_usd * conversion_rate
    return float("{:.2f}".format(price_myr))

@register.filter
def multiply(value, arg):
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return value
    
@register.filter
def reverse_queryset(queryset):
    return reversed(queryset)