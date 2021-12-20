from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def search_header(value):
    value = value.replace('\n\n', '</p><p>')
    return f"<p>{value}</p>"
