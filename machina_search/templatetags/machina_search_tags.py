from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def search_header(value):
    return f"<p>{value.replace('\n\n', '</p><p>')}</p>"
