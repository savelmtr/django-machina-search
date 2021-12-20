from django.db import models
import re
from django.conf import settings
from typing import Tuple, Set, Optional
from django.db.models.query import RawQuerySet
from machina_search import settings
from django.db import connection

if settings.SEARCH_ENGINE == 'postgres':
    from django.contrib.postgres.search import SearchQuery, SearchRank
    from django.db.models import F


class SearchManager(models.Manager):

    _search_from_statement = '''
        left join auth_user au
            on p.poster_id = au.id
        left join forum_conversation_topic fct
            on p.topic_id = fct.id
        left join forum_forum ff
            on fct.forum_id = ff.id
    '''

    def _search_helper(
        self, poster_name, search_forums: Set[int]) -> Tuple[str, str, str]:

        like_operator = \
            'ILIKE' \
            if settings.SEARCH_ENGINE == 'postgres' else \
            'LIKE'

        username_filter = f'''
            AND au.username {like_operator} '%{poster_name}%'
        ''' if poster_name else ''

        forums_filter = f'''
            AND fct.forum_id IN ({",".join(map(str, search_forums))})
        '''

        return username_filter, forums_filter

    def search(
        self,
        q: str,
        poster_name: str,
        search_forums: Set[int],
        search_topics: bool,
        page_num: int
    ) -> RawQuerySet:

        username_filter, forums_filter = self._search_helper(
            poster_name, search_forums)

        per_page = settings.TOPIC_POSTS_NUMBER_PER_PAGE
        start = page_num * per_page - per_page
        
        select_query = f'''
            fct.forum_id as forum_id,
            p.poster_id as poster_id,
            au.username as username,
            p.created as created,
            ff.slug as forum_slug,
            ff.id as forum_pk,
            fct.slug as topic_slug,
            fct.id as topic_pk,
            p.id as pk,
            p.subject as subject,
            p.content as content
        '''
        if settings.SEARCH_ENGINE == 'postgres':
            select_query += f", ts_headline('pg_catalog.{settings.SEARCH_LANGUAGE}'" \
                            f", p.content , query, 'StartSel=<mark>, StopSel=</mark>" \
                            f", MaxWords=40') as headline"
            search_vector_field = self._get_vector_field(search_topics)
            query = f'''
                select
                    {select_query},
                    ts_rank_cd({search_vector_field}, query) as rank
                from
                    machina_search_postssearchindex idx
                        left join forum_conversation_post p
                            on idx.topic = p.id
                        {self._search_from_statement},
                    websearch_to_tsquery('pg_catalog.{settings.SEARCH_LANGUAGE}', '{q}') query
                where
                    query @@ {search_vector_field}
                    {username_filter}
                    {forums_filter}
                order by rank desc
                limit {per_page} offset {start}
            '''
        else:
            search_filter = self._get_search_filter(
                q, search_topics
            )
            query = f'''
                select {select_query}
                from
                    forum_conversation_post p
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

    def search_count(
        self,
        q: str,
        poster_name: str,
        search_forums: Set[int],
        search_topics: bool,
    ) -> int:

        username_filter, forums_filter = self._search_helper(
            poster_name, search_forums)
        if settings.SEARCH_ENGINE == 'postgres':
            search_vector_field = self._get_vector_field(search_topics)
            count_query = f'''
                select count(p.id) as cnt
                from 
                    machina_search_postssearchindex idx
                        left join forum_conversation_post p
                            on idx.topic = p.id
                        {self._search_from_statement},
                    websearch_to_tsquery('pg_catalog.{settings.SEARCH_LANGUAGE}', '{q}') query
                where
                    query @@ {search_vector_field}
                    {username_filter}
                    {forums_filter}
            '''
        else:
            search_filter = self._get_search_filter(q, search_topics)
            count_query = f'''
                select count(id) as cnt
                from forum_conversation_post p
                    {self._search_from_statement}
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
