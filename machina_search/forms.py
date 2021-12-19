"""
    Forum search forms
    ==================

    This module defines forms provided by the ``forum_search`` application.

"""

from django import forms
from django.contrib.postgres import search
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from django.conf import settings
from machina.core.db.models import get_model
from machina.core.loading import get_class
# from .models import Post

if settings.SEARCH_ENGINE == 'postgres':
    from django.contrib.postgres.search import SearchQuery, SearchRank
    from django.db.models import F
import re


Forum = get_model('forum', 'Forum')

Post = get_model('forum_conversation', 'Post')

PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')

query_cleaning_pttrn = re.compile(r'[^\s\w\d]')


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
        return None

    def search(self, page_num):

        if not self.is_valid() or not self.cleaned_data.get('q'):
            return self.no_query_found()

        q = query_cleaning_pttrn.sub('', self.cleaned_data['q'])

        like_operator = \
            'ILIKE' \
            if settings.SEARCH_ENGINE == 'postgres' else \
            'LIKE'

        search_poster_name = self.cleaned_data.get(
            'search_poster_name', None)
        username_filter = f'''
            AND au.username {like_operator} '%{search_poster_name}%'
        ''' if search_poster_name else ''

        allowed_forum_ids = set(
            self.allowed_forums.values_list('id', flat=True))

        search_forums = {
            fid
            for fid in self.cleaned_data.get(
                'search_forums', [])
            if fid in allowed_forum_ids
        }
        forums_filter = f'''
            AND fct.forum_id IN ({",".join(map(str, search_forums))})
        ''' if search_forums != {} else f'''
            AND fct.forum_id IN ({",".join(map(str, allowed_forum_ids))})
        '''

        per_page = settings.TOPIC_POSTS_NUMBER_PER_PAGE
        start = page_num * per_page

        if settings.SEARCH_ENGINE == 'postgres':

            search_vector_field = \
                'search_vector_subject' \
                if self.cleaned_data.get('search_topics', None) else \
                'search_vector_all'
            count_query = f'''
                select count(id) as cnt
                from forum_conversation_post, plainto_tsquery('{q}') query
                where
                    query @@ {search_vector_field}
                    {username_filter}
                    {forums_filter}
            '''
            query = f'''
                select 
                    *,
                    ts_rank_cd({search_vector_field}, query) as rank
                from 
                    forum_conversation_post p 
                        left join auth_user au
                            on p.poster_id = au.id
                        left join forum_conversation_topic fct
                            on p.topic_id = fct.id,
                    plainto_tsquery('дальние огни') query
                where
                    query @@ {search_vector_field}
                    {username_filter}
                    {forums_filter}
                order by rank desc
                limit {per_page} offset {start}
            '''
            total_items_in_response = Post.objects.raw(count_query)[0]

        else:
            search_filter = \
                f'''
                    p.subject LIKE '%{q}%'
                ''' \
                if self.cleaned_data.get('search_topics', None) else \
                f'''
                    (p.subject LIKE '%{q}%'
                    or p.content LIKE '%{q}%')
                '''
            count_query = f'''
                select count(id) as cnt
                from forum_conversation_post
                where
                    {search_filter}
                    {username_filter}
                    {forums_filter}
            '''
            query = f'''
                select *
                from
                    forum_conversation_post p 
                        left join auth_user au
                            on p.poster_id = au.id
                        left join forum_conversation_topic fct
                            on p.topic_id = fct.id
                where
                    {search_filter}
                    {username_filter}
                    {forums_filter}
                order by p.updated desc
                limit {per_page} offset {start}
            '''
            total_items_in_response = Post.objects.raw(count_query)[0]

        total_pages = \
            total_items_in_response / per_page \
            if not total_items_in_response % per_page else \
            total_items_in_response // per_page + 1
        return Post.objects.raw(query), int(total_pages)
