"""
    Forum conversation models
    =========================

    This module defines models provided by the ``forum_conversation`` application.

"""

# from machina_search.abstract_models import AbstractPost
# from machina.core.db.models import model_factory
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from machina.apps.forum_conversation.abstract_models import AbstractPost as MachinaAbstractPost


if settings.SEARCH_ENGINE == 'postgres':
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.search import SearchVectorField


class Post(MachinaAbstractPost):
    """ Additions for postgres search in posts """

    # this fields are only for postgres search
    if settings.SEARCH_ENGINE == 'postgres':
        search_vector_all = SearchVectorField(null=True)
        search_vector_subject = SearchVectorField(null=True)

    class Meta:
        abstract = True
        app_label = 'forum_conversation'
        ordering = ['created', ]
        get_latest_by = 'created'
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

        # let's get index for our search_vector fields

        if settings.SEARCH_ENGINE == 'postgres':
            indexes = [
                GinIndex(fields=['search_vector_all']),
                GinIndex(fields=['search_vector_subject']),
            ]


# class Post = model_factory(AbstractPost)
