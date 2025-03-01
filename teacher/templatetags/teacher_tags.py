# school_manager/teacher/templatetags/teacher_tags.py
from django import template

register = template.Library()

@register.filter
def persian_numbers(value):
    persian_digits = {'0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴', '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'}
    return ''.join(persian_digits.get(char, char) for char in str(value))

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)