# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack

import os
import re
import glob
import zipfile

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
from distutils.command.build import build as BuildCommand


ROOT_PATH = os.path.dirname(
    os.path.realpath(__file__)
)

RESOURCE_PATH = os.path.join(
    ROOT_PATH, 'resource'
)

SOURCE_PATH = os.path.join(
    ROOT_PATH, 'source'
)

README_PATH = os.path.join(ROOT_PATH, 'README.rst')

with open(os.path.join(
    SOURCE_PATH, 'ftrack_connect_rv', '_version.py')
) as _version_file:
    VERSION = re.match(
        r'.*__version__ = \'(.*?)\'', _version_file.read(), re.DOTALL
    ).group(1)


class BuildRvPkg(BuildCommand):

    def initialize_options(self):
        '''Configure default options.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        self.rvpkg_src_dir = os.path.join(RESOURCE_PATH, 'plugin', 'src')

        self.resource_target_path = os.path.join(
            RESOURCE_PATH, 'plugin'
        )
        self.pakcage_name = 'ftrack-{0}.rvpkg'.format(VERSION)

    def run(self):
        '''build rvpkg'''
        out_path = os.path.join(self.resource_target_path, self.pakcage_name)
        with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as pkg:
            for f in os.listdir(self.rvpkg_src_dir):
                pkg.write(os.path.join(self.rvpkg_src_dir, f), arcname=f)


class Build(BuildCommand):
    def run(self):
        '''Run build ensuring build_resources called first.'''
        self.run_command('build_rvpkg')
        BuildCommand.run(self)


# Custom commands.
class PyTest(TestCommand):
    '''Pytest command.'''

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        '''Import pytest and run.'''
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


# Configuration.
setup(
    name='ftrack-connect-rv',
    version=VERSION,
    description='Repository for ftrack connect rv.',
    long_description=open(README_PATH).read(),
    keywords='',
    url='https://bitbucket.org/ftrack/ftrack-connect-rv',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={
        '': 'source'
    },
    setup_requires=[
        'sphinx >= 1.2.2, < 2',
        'sphinx_rtd_theme >= 0.1.6, < 2',
        'lowdown >= 0.1.0, < 1'
    ],
    install_requires=[
    ],
    tests_require=[
        'pytest >= 2.3.5, < 3'
    ],
    cmdclass={
        'test': PyTest,
        'build_rvpkg': BuildRvPkg,
        'build': Build
    },
    data_files=[
        (
            'ftrack_connect_rv_resource/hook',
            glob.glob(os.path.join(ROOT_PATH, 'resource', 'hook', '*.py'))
        )
    ]
)
