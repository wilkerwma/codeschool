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
        'django>=1.9',
        'django-model-utils',
        'django-picklefield',
        'pygments',
        'wagtail',
        'frozendict',
        'markdown',
        'django_jinja',
        'djinga',
        'djangorestframework',
        'django-annoying',
        'django-autoslug',
        'django-compressor',
        'slimit',
        'csscompressor',
        'html5lib',
        'django-extensions',
        'django-guardian',
        'pytz',
        'jinja2-django-tags',
        'django-bower',
        'django-address',
        'django-userena',
        'boxed>=0.3',
        'psutil',
        'pexpect',
        'unidecode',
        'fake-factory',
        'pygeneric',
        'lazy',

        # These are vendorized until they stabilize
        #'django-viewpack',
        #'ejudge>=0.3.6',
        #'iospec>=0.2.2',
        #'markio>=0.1.2',
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

