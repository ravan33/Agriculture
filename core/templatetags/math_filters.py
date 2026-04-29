"""
Custom template filters for the core app.
"""
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """
    Multiplies the value by the argument.
    Usage: {{ value|multiply:100 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter  
def percentage(value):
    """
    Converts a decimal to percentage.
    Usage: {{ 0.85|percentage }} -> 85%
    """
    try:
        return f"{float(value) * 100:.0f}%"
    except (ValueError, TypeError):
        return "0%"

@register.filter
def confidence_display(value):
    """
    Displays confidence score as a percentage with proper formatting.
    Usage: {{ confidence_score|confidence_display }}
    """
    try:
        confidence = float(value)
        if confidence <= 0:
            return "Unknown"
        percentage = confidence * 100
        return f"{percentage:.0f}% confidence"
    except (ValueError, TypeError):
        return "Unknown confidence"
