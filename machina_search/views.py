"""
    Forum search views
    ==================

    This module defines views provided by the ``forum_search`` application.

"""

from django.shortcuts import render
from django.views import View

from machina_search.forms import PostgresSearchForm


class PostgresSearchView(View):
    """
        Allows to search within forums,
        can use postgres search.
    """

    form_class = PostgresSearchForm
    template = 'machina_search/search.html'

    def get(self, request, *args, **kwargs):

        form = self.form_class(request)

        if 'q' in request.GET:
            page_num = request.GET.get('page', 1)
            result, total_pages = form.search(page_num)
            context = {
                'form': form,
                'result_count': total_pages,
                'query': form.cleaned_data.get('q'),
                'page': result
            }
        else:
            context = {
                'form': form,
                'query': False,
            }

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        self.get(request, *args, **kwargs)
