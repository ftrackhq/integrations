# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import os
import sys
import shutil
from distutils.spawn import find_executable

import subprocess

from setuptools import setup, find_packages, Command

import fileinput


ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
SOURCE_PATH = os.path.join(ROOT_PATH, 'source')
README_PATH = os.path.join(ROOT_PATH, 'README.md')
RESOURCE_PATH = os.path.join(ROOT_PATH, 'resource')
RESOURCE_TARGET_PATH = os.path.join(
    SOURCE_PATH, 'ftrack_nuke_studio', 'resource.py'
)
HIERO_PLUGIN_PATH = os.path.join(RESOURCE_PATH, 'plugin')
BUILD_PATH = os.path.join(ROOT_PATH, 'build')
STAGING_PATH = os.path.join(BUILD_PATH, 'ftrack-nuke-studio-{0}')
HOOK_PATH = os.path.join(RESOURCE_PATH, 'hook')
APPLICATION_HOOK_PATH = os.path.join(RESOURCE_PATH, 'application_hook')


# Custom commands.
class BuildResources(Command):
    '''Build additional resources.'''

    user_options = []

    def initialize_options(self):
        '''Configure default options.'''

    def finalize_options(self):
        '''Finalize options to be used.'''
        self.resource_source_path = os.path.join(
            RESOURCE_PATH, 'resource.qrc'
        )
        self.resource_target_path = RESOURCE_TARGET_PATH

    def _replace_imports_(self):
        '''Replace imports in resource files to Qt instead of QtCore.

        This allows the resource file to work with many different versions of
        Qt.

        '''
        replace = r'from Qt import QtCore'
        for line in fileinput.input(self.resource_target_path, inplace=True, mode='r'):
            if r'import QtCore' in line:
                # Calling print will yield a new line in the resource file.
                sys.stdout.write(line.replace(line, replace))
            else:
                sys.stdout.write(line)

    def run(self):
        '''Run build.'''
        try:
            pyside_rcc_command = 'pyside2-rcc'
            executable = None

            # Check if the command for pyside*-rcc is in executable paths.
            if find_executable(pyside_rcc_command):
                executable = pyside_rcc_command

            if not executable:
                raise IOError('Not executable found for pyside2-rcc ')

            # Use the first occurrence if more than one is found.
            cmd = [
                executable,
                '-o',
                self.resource_target_path,
                self.resource_source_path
            ]
            print('running : {}'.format(cmd))
            subprocess.check_call(cmd)

        except (subprocess.CalledProcessError, OSError):
            raise RuntimeError(
                'Error compiling resource.py using pyside-rcc. Possibly '
                'pyside-rcc could not be found. You might need to manually add '
                'it to your PATH. See README for more information.'
            )

        self._replace_imports_()



class BuildPlugin(Command):
    '''Build plugin.'''

    description = 'Download dependencies and build plugin .'

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        '''Run the build step.'''
        import setuptools_scm
        release = setuptools_scm.get_version(version_scheme='post-release')
        VERSION = '.'.join(release.split('.')[:3])
        global STAGING_PATH
        STAGING_PATH = STAGING_PATH.format(VERSION)

        # Clean staging path
        shutil.rmtree(STAGING_PATH, ignore_errors=True)

        # build resources
        self.run_command('build_resources')

        # Copy plugin files
        shutil.copytree(
            HIERO_PLUGIN_PATH,
            os.path.join(STAGING_PATH, 'resource')
        )

        # Copy hook files
        shutil.copytree(
            HOOK_PATH,
            os.path.join(STAGING_PATH, 'hook')
        )

        # Copy applipcation hooks files
        shutil.copytree(
            APPLICATION_HOOK_PATH,
            os.path.join(STAGING_PATH, 'application_hook')
        )


        dependencies_path = os.path.join(STAGING_PATH, 'dependencies')


        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install','.','--target',
            dependencies_path]
        )

        shutil.make_archive(
            os.path.join(
                BUILD_PATH,
                'ftrack-nuke-studio-{0}'.format(VERSION)
            ),
            'zip',
            STAGING_PATH
        )

version_template = '''
# :coding: utf-8
# :copyright: Copyright (c) 2017-2021 ftrack

__version__ = {version!r}
'''


# Call main setup.
setup(
    name='ftrack-nuke-studio',
    description='ftrack integration with NUKE STUDIO.',
    long_description=open(README_PATH).read(),
    keywords='ftrack, integration, connect, the foundry, nuke, studio',
    url='https://github.com/ftrackhq/integrations/projects/nuke-studio',
    author='ftrack',
    author_email='support@ftrack.com',
    license='Apache License (2.0)',
    packages=find_packages(SOURCE_PATH),
    package_dir={'': 'source'},
    package_data={"": ["{}/**/*.*".format(RESOURCE_PATH)]},
    version="2.5.2",
    setup_requires=[
        'PySide2 >=5, <6',
        'Qt.py >=1.0.0, < 2',
        'sphinx >= 1.8.5, < 4',
        'sphinx_rtd_theme >= 0.1.6, < 1',
        'lowdown >= 0.1.0, < 1',
        'setuptools>=45.0.0',
        'setuptools_scm'
    ],
    install_requires=[
        'clique==1.6.1',
        'appdirs == 1.4.0',
        'lucidity >= 1.5, < 2',
        'opentimelineio ==0.11',
        'qt.py >=1.0.0, < 2',
        'ftrack-python-api'
    ],
    zip_safe=False,
    cmdclass={
        'build_plugin': BuildPlugin,
        'build_resources': BuildResources
    },
    python_requires=">=3, <4.0"
)
