from django import template
from django.db.models import Avg
import math

register = template.Library()

@register.filter
def average(queryset, field_name):
    """Return the average of the given field in a queryset."""
    if not queryset.exists():
        return 0
    result = queryset.aggregate(avg=Avg(field_name))
    return round(result["avg"] or 0, 1)

@register.filter
def times(number):
    """Returns a range for looping (e.g., 3 → range(3))."""
    return range(int(number))

@register.filter
def remainder_stars(rating):
    """Returns how many empty stars to show (out of 5)."""
    return range(5 - int(math.floor(rating)))
