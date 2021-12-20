from machina_search import settings
from django.db import models
from .managers import SearchManager
if settings.SEARCH_ENGINE == 'postgres':
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.search import SearchVectorField


class PostsSearchIndex(models.Model):
    """ For postgres search in posts """

    # this fields are only for postgres search
    if settings.SEARCH_ENGINE == 'postgres':
        topic = models.IntegerField(unique=True, primary_key=True)
        search_vector_all = SearchVectorField(null=True)
        search_vector_subject = SearchVectorField(null=True)

    objects = SearchManager()

    class Meta:
        app_label = 'machina_search'
        verbose_name = 'post_search_index'
        # let's get index for our search_vector fields
        if settings.SEARCH_ENGINE == 'postgres':
            indexes = [
                GinIndex(fields=['search_vector_all']),
                GinIndex(fields=['search_vector_subject']),
            ]
