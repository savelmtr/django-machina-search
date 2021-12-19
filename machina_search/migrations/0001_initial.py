# Generated by Django 4.0 on 2021-12-19 17:33

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations, models
import django.db.models.deletion
from machina_search import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('forum_conversation', '0011_remove_post_poster_ip'),
    ]
    if settings.SEARCH_ENGINE == 'postgres':
        operations = [
            migrations.CreateModel(
                name='PostsSearchIndex',
                fields=[
                    ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                    ('content', models.TextField()),
                    ('subject', models.CharField(max_length=255)),
                    ('search_vector_all', django.contrib.postgres.search.SearchVectorField(null=True)),
                    ('search_vector_subject', django.contrib.postgres.search.SearchVectorField(null=True)),
                    ('topic', models.IntegerField(unique=True)),
                ],
                options={
                    'verbose_name': 'post_search_index'
                },
            ),
            migrations.AddIndex(
                model_name='postssearchindex',
                index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector_all'], name='machina_sea_search__36ffc7_gin'),
            ),
            migrations.AddIndex(
                model_name='postssearchindex',
                index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector_subject'], name='machina_sea_search__a65633_gin'),
            ),
        ]
