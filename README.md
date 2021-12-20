# Django-machina search
Search module for forum engine [django-machina](https://github.com/ellmetha/django-machina). It performs search using postgres full text search engine or sqlite `LIKE` queries.

## Installation
You may perform these commands in you environment:

```
git clone https://github.com/savelmtr/django-machina-search
pip install -r django-machina-search/requirements.txt
pip install django-machina-search
```
After the package has installed, you may add it into `INSTALLED_APPS` in `settings.py` of your project. Just like this, after django-machina apps:
 ```
 INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    # Machina apps:
    'machina',
    'machina.apps.forum',
    'machina.apps.forum_conversation',
    'machina.apps.forum_conversation.forum_attachments',
    'machina.apps.forum_conversation.forum_polls',
    'machina.apps.forum_feeds',
    'machina.apps.forum_moderation',
    'machina.apps.forum_search',
    'machina.apps.forum_tracking',
    'machina.apps.forum_member',
    'machina.apps.forum_permission',
    
    # Machina search
    'machina_search'
 ]
 ```
 Please, don't forget to add `'machina_search'` only **after** `machina`. It is important.

## Configs

The only config we have with the search is **SEARCH_LANGUAGE**. You can paste it into `settings.py`. For example:
```
SEARCH_LANGUAGE = 'english'
```
in place of _english_ can also be russian, french, finnish, german - in other words, any language supported by postgres.
