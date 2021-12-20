from django import template
from django.template.defaultfilters import stringfilter
from machina.models.fields import render_func


register = template.Library()

@register.filter
@stringfilter
def search_header(value):
    return render_func(value).replace('[mark]', '<mark>').replace('[/mark]', '</mark>')
