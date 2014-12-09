# :coding: utf-8
# :copyright: Copyright (c) 2014 ftrack

import os
from ftrack import Registry

PROCESSOR_PLUGINS = Registry(os.environ.get('FTRACK_PROCESSOR_PLUGIN_PATH', '').split(os.pathsep))

def setup():
    global PROCESSOR_PLUGINS
    PROCESSOR_PLUGINS.discover()

global PROCESSOR_PLUGINS
