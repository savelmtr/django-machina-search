from django import template
from django.template.defaultfilters import stringfilter
from machina.models.fields import render_func
import re


register = template.Library()

@register.filter
@stringfilter
def search_header(value: str) -> str:
    return render_func(value).replace('[mark]', '<mark>').replace('[/mark]', '</mark>')


@register.simple_tag(takes_context=True)
def insert_page_in_url(context: dict, num: int) -> str:
    url = context['request'].get_full_path()
    if 'page=' in url:
        url = re.sub(r'page=\d*', f'page={num}', url)
    else:
        url += f'&page={num}'
