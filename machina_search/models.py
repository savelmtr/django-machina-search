"""
    Forum conversation models
    =========================

    This module defines models provided by the ``forum_conversation`` application.

"""

from machina_search.abstract_models import AbstractPost
from machina.core.db.models import model_factory


Post = model_factory(AbstractPost)
