# -*- coding: utf-8 -*-
from setuptools import setup

packages = ['oscar_odin', 'oscar_odin.mappings', 'oscar_odin.resources']

package_data = {'': ['*'], 'oscar_odin': ['fixtures/oscar_odin/*']}

install_requires = ['django-oscar>=3.2,<4.0', 'odin>=2.9,<3.0']

setup_kwargs = {
    'name': 'django-oscar-odin',
    'version': '0.1.0',
    'description': 'Odin Resources and mappings to Oscar models',
    'long_description': '# Oscar Odin\n\n',
    'author': 'Tim Savage',
    'author_email': 'tim@savage.company',
    'maintainer': 'None',
    'maintainer_email': 'None',
    'url': 'https://github.com/django-oscar/oscar-odin',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
