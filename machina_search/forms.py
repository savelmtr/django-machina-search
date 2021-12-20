from typing import Tuple
from django import forms
from django.utils.translation import gettext_lazy as _

from machina.core.db.models import get_model
from machina.core.loading import get_class
from django.db.models.query import RawQuerySet
import re
from .models import PostsSearchIndex


Forum = get_model('forum', 'Forum')

PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')


class PostgresSearchForm(forms.Form):

    query_cleaning_pttrn = re.compile(r'[^\s\w\d]')

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

        self.allowed_forums = set(PermissionHandler().get_readable_forums(
            Forum.objects.all(), user
        ))
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

        if not self.is_valid() or not self.cleaned_data['q']:
            return self.no_query_found()
        if self.cleaned_data['q']:
            q = self.query_cleaning_pttrn.sub(
                '', self.cleaned_data['q'])
        poster_name = self.query_cleaning_pttrn.sub(
            '', self.cleaned_data['search_poster_name']) \
            if self.cleaned_data['search_poster_name'] else None
        search_forums = set(map(int, self.cleaned_data.get('search_forums', [])))
        allowed_forums_ids = {f.pk for f in self.allowed_forums}
        search_forums = {
            fid for fid in search_forums
            if fid in allowed_forums_ids
        } if len(search_forums) else allowed_forums_ids

        result = PostsSearchIndex.objects.search(
            q=q,
            poster_name=poster_name,
            search_forums=search_forums,
            page_num=page_num,
            search_topics=self.cleaned_data['search_topics']
        )
        total = PostsSearchIndex.objects.search_count(
            q=q,
            poster_name=poster_name,
            search_forums=search_forums,
            search_topics=self.cleaned_data['search_topics']
        )
        return result, total
