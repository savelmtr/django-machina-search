from django.db import models
import re
from django.conf import settings
from typing import Tuple, Set, Optional
from django.db.models.query import RawQuerySet
from machina_search import settings
from django.db import connection


query_cleaning_pttrn = re.compile(r'[^\s\w\d]')


class PostManager(models.Manager):

    _search_from_statement = '''
        forum_conversation_post p
            left join auth_user au
                on p.poster_id = au.id
            left join forum_conversation_topic fct
                on p.topic_id = fct.id
            left join forum_forum ff
                on fct.forum_id = ff.id
    '''

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

        search_forums = cleaned_data.get('search_forums', None)
        search_forums = {
            fid for fid in search_forums
            if fid in allowed_forum_ids and type(fid) == int
        } if search_forums else allowed_forum_ids
        forums_filter = f'''
            AND fct.forum_id IN ({",".join(map(str, search_forums))})
        '''

        return q, username_filter, forums_filter

    def search(self, cleaned_data: dict, allowed_forum_ids: Set[int], page_num: int) -> RawQuerySet:

        q, username_filter, forums_filter = self._search_helper(
            cleaned_data, allowed_forum_ids)

        per_page = settings.TOPIC_POSTS_NUMBER_PER_PAGE
        start = page_num * per_page - per_page
        
        select_query = '''
            fct.forum_id as forum_id,
            p.poster_id as poster_id,
            au.username as username,
            p.created as created,
            p._content_rendered as content_rendered,
            ff.slug as forum_slug,
            ff.id as forum_pk,
            fct.slug as topic_slug,
            fct.id as topic_pk,
            p.id as pk,
            p.subject as subject,
            p.content as content
        '''
        if settings.SEARCH_ENGINE == 'postgres':
            search_vector_field = self._get_vector_field(
                cleaned_data.get('search_topics', False)
            )
            query = f'''
                select
                    {select_query},
                    ts_rank_cd({search_vector_field}, query) as rank
                from
                    {self._search_from_statement},
                    plainto_tsquery('{q}') query
                where
                    query @@ {search_vector_field}
                    {username_filter}
                    {forums_filter}
                order by rank desc
                limit {per_page} offset {start}
            '''
        else:
            search_filter = self._get_search_filter(
                q, cleaned_data.get('search_topics', False)
            )
            query = f'''
                select {select_query}
                from
                    {self._search_from_statement}
                where
                    {search_filter}
                    {username_filter}
                    {forums_filter}
                order by p.updated desc
                limit {per_page} offset {start}
            '''
        with connection.cursor() as cursor:
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    def count_search_pages(self, cleaned_data: dict, allowed_forum_ids: Set[int]) -> int:

        q, username_filter, forums_filter = self._search_helper(
            cleaned_data, allowed_forum_ids)
        if settings.SEARCH_ENGINE == 'postgres':
            search_vector_field = self._get_vector_field(
                cleaned_data.get('search_topics', False)
            )
            count_query = f'''
                select count(p.id) as cnt
                from 
                    {self._search_from_statement},
                    plainto_tsquery('{q}') query
                where
                    query @@ {search_vector_field}
                    {username_filter}
                    {forums_filter}
            '''
        else:
            search_filter = self._get_search_filter(
                q, cleaned_data.get('search_topics', False))
            count_query = f'''
                select count(id) as cnt
                from {self._search_from_statement}
                where
                    {search_filter}
                    {username_filter}
                    {forums_filter}
            '''
        with connection.cursor() as cursor:
            cursor.execute(count_query)
            total_items_in_response = int(cursor.fetchone()[0])
        return int(total_items_in_response)

    def _get_search_filter(self, q: str, search_topics: Optional[bool]) -> str:
        return f'''
            p.subject LIKE '%{q}%'
        ''' \
        if search_topics else \
        f'''
            (p.subject LIKE '%{q}%'
            or p.content LIKE '%{q}%')
        '''

    def _get_vector_field(self, search_topics: Optional[bool]) -> str:
        return 'search_vector_subject' \
            if search_topics else \
            'search_vector_all'
