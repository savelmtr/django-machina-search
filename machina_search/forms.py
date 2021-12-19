"""
    Forum search forms
    ==================

    This module defines forms provided by the ``forum_search`` application.

"""

from typing import Tuple
from django import forms
from django.utils.translation import gettext_lazy as _

from django.conf import settings
from machina.core.db.models import get_model
from machina.core.loading import get_class
from .managers import PostManager
from django.db.models.query import RawQuerySet


Forum = get_model('forum', 'Forum')

Post = get_model('forum_conversation', 'Post')
Post.objects = PostManager()

PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')


class PostgresSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label=_('Search'),
        widget=forms.TextInput(attrs={'type': 'search'})
    )

    search_topics = forms.BooleanField(
        label=_('Search only in topic subjects'),
        required=False
    )

    search_poster_name = forms.CharField(
        label=_('Search for poster'),
        help_text=_(
            'Enter a user name to limit '
            'the search to a specific user.'
        ),
        max_length=255, required=False,
    )

    search_forums = forms.MultipleChoiceField(
        label=_('Search in specific forums'),
        help_text=_('Select the forums you wish to search in.'),
        required=False,
    )

    def __init__(self, request):
        user = request.user

        super().__init__(request.GET)

        # Update some fields
        self.fields['q'].label = _('Search for keywords')
        self.fields['q'].widget.attrs['placeholder'] = \
            _('Keywords or phrase')
        self.fields['search_poster_name'].widget.attrs['placeholder'] = \
            _('Poster name')

        self.allowed_forums = PermissionHandler().get_readable_forums(
            Forum.objects.all(), user
        )
        if self.allowed_forums:
            self.fields['search_forums'].choices = [
                (f.id, '{} {}'.format('-' * f.margin_level, f.name))
                for f in self.allowed_forums
            ]
        else:
            # The user cannot view any single forum, the 'search_forums' field can be deleted
            del self.fields['search_forums']

    def no_query_found(self):
        return None, 0

    def search(self, page_num: int) -> Tuple[RawQuerySet, int]:

        if not self.is_valid() or not self.cleaned_data.get('q'):
            return self.no_query_found()

        allowed_forum_ids = set(
            self.allowed_forums.values_list('id', flat=True))

        result: RawQuerySet = Post.objects.search(
            self.cleaned_data, allowed_forum_ids, page_num)
        total_pages: int = Post.objects.count_search_pages(
            self.cleaned_data, allowed_forum_ids)

        return result, total_pages
