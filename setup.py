# :coding: utf-8

import os
import re

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.rst')


# Read version from source.
with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_nuke_studio', '_version.py'
)) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


# Call main setup.
setup(
    name='ftrack-connect-nuke-studio',
    version=VERSION,
    description='ftrack integration with NUKE STUDIO.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, integration, connect, the foundry, nuke, studio',
    url='https://bitbucket.org/ftrack/ftrack-connect-nuke-studio',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2'
    ],
    install_requires=[
    ],
    tests_require=[
    ],
    zip_safe=False
)
