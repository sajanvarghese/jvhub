from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
@register.filter
def calc_day_total(orders):
    return sum(order.quantity * order.product.price for order in orders)