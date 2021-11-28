"""
    Forum search URLs
    =================

    This module defines URL patterns associated with the django-machina's ``forum_search``
    application.

"""

from django.urls import path

from .views import PostgresSearchView


app_name = 'machina_search'

urlpatterns = [
    path('', PostgresSearchView.as_view(), name='search')
]
