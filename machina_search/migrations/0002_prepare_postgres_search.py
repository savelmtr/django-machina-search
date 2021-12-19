# Generated by Django 2.2.9 on 2020-01-30 19:40

from django.db import migrations
from machina_search import settings


class Migration(migrations.Migration):

    dependencies = [
        ('machina_search', '0001_initial'),
    ]

    if settings.SEARCH_ENGINE == 'postgres':
        operations = [
            migrations.RunSQL(
                    sql='''
                    CREATE FUNCTION update_search_table() RETURNS trigger AS $machina_search_post_search_index$
                        BEGIN
                            IF (TG_OP = 'UPDATE' OR TG_OP = 'INSERT') THEN
                                INSERT into machina_search_post_search_index (topic_id, subject, content)
                                SELECT NEW.id, NEW.subject, NEW.content
                                ON CONFLICT ("topic_id") 
                                DO UPDATE SET "subject" = EXCLUDED.subject, "content" = EXCLUDED.content;
                            END IF;    
                            RETURN NEW;
                        END;
                    $machina_search_post_search_index$ LANGUAGE plpgsql;

                    CREATE TRIGGER post_search_index_add 
                        AFTER INSERT OR UPDATE ON forum_conversation_post
                        FOR EACH ROW EXECUTE PROCEDURE update_search_table();

                    CREATE TRIGGER post_update_trigger_all
                    BEFORE INSERT OR UPDATE OF subject, content, search_vector_all
                    ON machina_search_post_search_index
                    FOR EACH ROW EXECUTE PROCEDURE
                    tsvector_update_trigger(
                      search_vector_all, 'pg_catalog.{0}', subject, content);

                    CREATE TRIGGER post_update_trigger_subject
                    BEFORE INSERT OR UPDATE OF subject, search_vector_subject
                    ON machina_search_post_search_index
                    FOR EACH ROW EXECUTE PROCEDURE
                    tsvector_update_trigger(
                      search_vector_subject, 'pg_catalog.{0}', subject);

                    UPDATE machina_search_post_search_index
                    SET search_vector_all = NULL, search_vector_subject = NULL;
                    '''.format(settings.SEARCH_LANGUAGE),

                    reverse_sql='''
                    DROP TRIGGER IF EXISTS post_update_trigger_all, post_update_trigger_subject
                    ON machina_search_post_search_index;
                    DROP TRIGGER IF EXISTS post_search_index_add ON forum_conversation_post;
                    '''),
        ]
    else:
        operations = []
