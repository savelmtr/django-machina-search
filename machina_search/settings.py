from django.conf import settings
from machina.conf import settings as machina_conf

TOPIC_POSTS_NUMBER_PER_PAGE = getattr(machina_conf, 'TOPIC_POSTS_NUMBER_PER_PAGE', 15)
SEARCH_ENGINE = 'postgres' \
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql' else \
    'default'
SEARCH_LANGUAGE = getattr(settings, 'SEARCH_LANGUAGE', 'english')
