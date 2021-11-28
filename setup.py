import re
from pathlib import Path

from setuptools import find_packages, setup

HERE = Path(__file__).parent

setup(
    name='machina_search',
version=re.search(r"__version__\s*?=\s*?'(.*?)'", open(HERE/'machina_search/__init__.py').read()).group(1),
    description='Postgres search for django-machina.',
    long_description=open(HERE/'README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/savelmtr/django-machina-search',
    packages=find_packages(include=['machina_search', 'machina_search.*']),
    install_requires=open(HERE/'requirements.txt').read().split('\n'),
    include_package_data=True,
    test_suite='tests',
)