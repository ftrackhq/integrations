# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

import ftrack
ftrack.setup()


from ._version import __version__


PROCESSOR_PLUGINS = ftrack.Registry(
    os.environ.get('FTRACK_PROCESSOR_PLUGIN_PATH', '').split(os.pathsep)
)


def setup():
    '''Setup package.'''
    PROCESSOR_PLUGINS.discover()
