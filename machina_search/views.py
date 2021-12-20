"""
    Forum search views
    ==================

    This module defines views provided by the ``forum_search`` application.

"""

from django.shortcuts import render
from django.views import View
from machina_search import settings
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
            result, count_results = form.search(page_num)
            per_page = settings.TOPIC_POSTS_NUMBER_PER_PAGE
            total_pages = int(count_results / per_page
                if not count_results % per_page else
                count_results // per_page + 1)
            context = {
                'form': form,
                'result_count': count_results,
                'query': form.cleaned_data['q'],
                'results': result,
                'has_previous': page_num > 1,
                'has_next': page_num < total_pages,
                'is_paginated': total_pages > 1,
                'previous_page_number': page_num - 1 if page_num > 1 else 1,
                'next_page_number': page_num + 1 if page_num < total_pages else total_pages,
                'page_range': range(1, total_pages + 1),
                'page_num': page_num,
                'total_pages': total_pages,
            }
        else:
            context = {
                'form': form,
                'query': False,
            }

        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        self.get(request, *args, **kwargs)
