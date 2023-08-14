from django import template

register = template.Library()

@register.filter
def convert_to_myr(price_usd):
    conversion_rate = 4.55
    price_myr = price_usd * conversion_rate
    return "RM {:.2f}".format(price_myr)