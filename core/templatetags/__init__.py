"""
Custom template filters for the core app.
"""
from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument.
    Usage: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter 
def percentage(value):
    """
    Converts a decimal to percentage.
    Usage: {{ 0.85|percentage }} returns 85
    """
    try:
        return int(float(value) * 100)
    except (ValueError, TypeError):
        return 0
