# -*- coding: utf8 -*-
#
# This file were created by Python Boilerplate. Use boilerplate to start simple
# usable and best-practices compliant Python projects.
#
# Learn more about it at: http://github.com/fabiommendes/boilerplate/
#

import os
from setuptools import setup, find_packages


# Meta information
name = 'codeschool'
author = 'Fábio Macêdo Mendes'
version = open('VERSION').read().strip()
dirname = os.path.dirname(__file__)


# Save version and author to __meta__.py
with open(os.path.join(dirname, 'src', name, '__meta__.py'), 'w') as F:
    F.write('__version__ = %r\n__author__ = %r\n' % (version, author))


setup(
    # Basic info
    name=name,
    version=version,
    author=author,
    author_email='fabiomacedomendes@gmail.com',
    url='',
    description='A short description for your project.',
    long_description=open('README.rst').read(),

    # Classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],

    # Packages and depencies
    package_dir={'': 'src'},
    packages=find_packages('src'),
    package_data={
        '': [
            'templates/*.*',
            'templates/*/*.*',
            'templates/*/*/*.*',
            'templates/*/*/*/*.*'],  # this is ridiculous. is there a better
                                     # option in setuptools?
        'codeschool': [
            'static/*.*',
            'static/*/*.*',
            'static/*/*/*.*'],
    },
    install_requires=[
        # Non-django dependencies
        'pygments',
        'frozendict',
        'markdown',
        'csscompressor',
        'html5lib',
        'slimit',
        'unidecode',
        'pygeneric',
        'lazy',
        'fake-factory',
        'pytz',

        # Django and extensions
        'django>=1.9',
        'django-model-utils',
        'django-picklefield',
        'django-jsonfield',
        'django-annoying',
        'django-autoslug',
        'django-compressor',
        'django-extensions',
        'django-guardian',
        'django-bower',
        'django-userena',
        'django-polymorphic',
        'django-filter',
        'djangorestframework',
        'jsonfield',

        # Wagtail
        'wagtail',
        'wagtailfontawesome',
        'wagtailgmaps',
        'wagtailosm',
        # 'wagtailembedder',  (vendorized until it lands on pip)
        # 'wagtail-markdown', (vendorized until it lands on pip)

        # Jinja support
        'jinja2',
        'django_jinja',
        'djinga',
        'jinja2-django-tags',

        # 'ejudge', (vendorized)
        'boxed>=0.3',
        'psutil',
        'pexpect',

        # 'django-viewpack', (vendorized)

        # 'markio', (vendorized)
        # 'iospec', (vendorized)
        'mistune',
    ],
    extras_require={
        'testing': ['pytest'],
    },

    # Scripts
    entry_points={
        'console_scripts': ['codeschool = codeschool.__main__:main'],
    },

    # Other configurations
    zip_safe=False,
    platforms='any',
    license='GPL',
    test_suite='%s.test.test_%s' % (name, name),
)
