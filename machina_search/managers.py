from django.contrib.postgres import search
from django.db import models
import re
from django.conf import settings
from typing import Tuple, Set

query_cleaning_pttrn = re.compile(r'[^\s\w\d]')


class PostManager(models.Manager):

    def _search_helper(
        self, cleaned_data: dict, allowed_forum_ids: Set[int]) -> Tuple[str, str, str]:

        q = query_cleaning_pttrn.sub('', cleaned_data['q'])

        like_operator = \
            'ILIKE' \
            if settings.SEARCH_ENGINE == 'postgres' else \
            'LIKE'

        search_poster_name = query_cleaning_pttrn.sub(
            '',
            cleaned_data.get('search_poster_name', '')
        )
        username_filter = f'''
            AND au.username {like_operator} '%{search_poster_name}%'
        ''' if search_poster_name else ''

        search_forums = {
            fid
            for fid in cleaned_data.get(
                'search_forums', [])
            if fid in allowed_forum_ids and type(fid) == int
        }
        forums_filter = f'''
            AND fct.forum_id IN ({",".join(map(str, search_forums))})
        ''' if search_forums != {} else f'''
            AND fct.forum_id IN ({",".join(map(str, allowed_forum_ids))})
        '''
        return q, username_filter, forums_filter

    def search(self, cleaned_data, allowed_forum_ids, page_num):

        q, username_filter, forums_filter = self._search_helper(
            cleaned_data, allowed_forum_ids)

        per_page = settings.TOPIC_POSTS_NUMBER_PER_PAGE
        start = page_num * per_page - per_page

        if settings.SEARCH_ENGINE == 'postgres':
            search_vector_field = self._get_vector_field(
                cleaned_data.get('search_topics', None)
            )
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
        else:
            search_filter = self._get_search_filter(
                q, cleaned_data.get('search_topics', None)
            )
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
        return self.raw(query)

    def count_search_pages(self, cleaned_data, allowed_forum_ids) -> int:

        q, username_filter, forums_filter = self._search_helper(
            cleaned_data, allowed_forum_ids)
        per_page = settings.TOPIC_POSTS_NUMBER_PER_PAGE
        if settings.SEARCH_ENGINE == 'postgres':
            search_vector_field = self._get_vector_field(
                cleaned_data.get('search_topics', None)
            )
            count_query = f'''
                select count(id) as cnt
                from forum_conversation_post, plainto_tsquery('{q}') query
                where
                    query @@ {search_vector_field}
                    {username_filter}
                    {forums_filter}
            '''
        else:
            search_filter = self._get_search_filter(
                q, cleaned_data.get('search_topics', None))
            count_query = f'''
                select count(id) as cnt
                from forum_conversation_post
                where
                    {search_filter}
                    {username_filter}
                    {forums_filter}
            '''
        total_items_in_response = self.raw(count_query)[0]
        return total_items_in_response / per_page \
            if not total_items_in_response % per_page else \
            total_items_in_response // per_page + 1

    def _get_search_filter(self, q, search_topics) -> str:
        return f'''
            p.subject LIKE '%{q}%'
        ''' \
        if search_topics else \
        f'''
            (p.subject LIKE '%{q}%'
            or p.content LIKE '%{q}%')
        '''

    def _get_vector_field(self, search_topics) -> str:
        return 'search_vector_subject' \
            if search_topics else \
            'search_vector_all'
