# django-machina-search
Search module for forum engine django-machina. It performs search using postgres full-text search engine or sqlite icontains queries.

# Configs

SEARCH_ENGINE = 'default' or 'postgres'
SEARCH_LANGUAGE = 'english' or any other one that is supported by PG (like 'russian')