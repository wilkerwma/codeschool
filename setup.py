#-*- coding: utf8 -*-
import os
import setuptools
from setuptools import setup

VERSION = '0.1a1'
AUTHOR = 'Fábio Macêdo Mendes'

#
# Create meta.py file with updated version/author info
#
base, _ = os.path.split(__file__)
path = os.path.join(base, 'src', 'codeschool', 'meta.py')
with open(path, 'w') as F:
    F.write(
        '# Auto-generated file. Please do not edit\n'
        '__version__ = %r\n' % VERSION +
        '__author__ = %r\n' % AUTHOR)

#
# Main configuration script
#
setup(
    name='codeschool',
    version=VERSION,
    description='Simple online judge for Django for Python and Pytuguês files',
    author='Fábio Macêdo Mendes',
    author_email='fabiomacedomendes@gmail.com',
    url='https://github.com/fabiommendes/codeschool',
    long_description=(
        r'''...'''),

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],

    package_dir={'': 'src'},
    packages=setuptools.find_packages('src'),
    license='GPL',
)
