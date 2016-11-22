# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import pyblish.plugin

from ._version import __version__


def register_shared_pyblish_plugins():
    '''Register shared pyblish plugins.'''
    path = os.path.normpath(
        os.path.join(
            os.path.abspath(
                os.path.dirname(
                    __file__
                )
            ),
            'shared_pyblish_plugins'
        )
    )
    print 'REGISTER PLUGINS HERE:', path
    pyblish.plugin.register_plugin_path(path)
