# :coding: utf-8
# :copyright: Copyright (c) 2016 ftrack

import os
import pyblish.plugin


def register_shared_plugins():
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
    pyblish.plugin.register_plugin_path(path)
