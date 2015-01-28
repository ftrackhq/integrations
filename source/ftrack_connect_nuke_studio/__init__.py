# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os

from ftrack import Registry

from ._version import __version__


PROCESSOR_PLUGINS = Registry(
    os.environ.get('FTRACK_PROCESSOR_PLUGIN_PATH', '').split(os.pathsep)
)


def setup():
    '''Setup package.'''
    PROCESSOR_PLUGINS.discover()
