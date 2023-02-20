from django.db import migrations
from machina_search import settings


class Migration(migrations.Migration):

    dependencies = [
        ('machina_search', '0002_prepare_postgres_search'),
    ]

    if settings.SEARCH_ENGINE == 'postgres':
        operations = [
            migrations.RunSQL(
                    sql='''
                    INSERT into machina_search_postssearchindex 
                        (topic, search_vector_all, search_vector_subject)
                    (
                        SELECT
                            p.id,
                            setweight(to_tsvector('pg_catalog.{0}', coalesce(p.subject, '')), 'A') ||
                            setweight(to_tsvector('pg_catalog.{0}', coalesce(p.content, '')), 'B'),
                            to_tsvector('pg_catalog.{0}', coalesce(p.subject, ''))
                        FROM forum_conversation_post p
                    )
                    ON CONFLICT ("topic") 
                    DO UPDATE SET
                        "search_vector_all" = EXCLUDED.search_vector_all,
                        "search_vector_subject" = EXCLUDED.search_vector_subject;
                    '''.format(settings.SEARCH_LANGUAGE),

                    reverse_sql='''
                    TRUNCATE machina_search_postssearchindex;
                    '''),
        ]
    else:
        operations = []
