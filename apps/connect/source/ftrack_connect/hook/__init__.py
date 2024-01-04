# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import os

# Hooks use the ftrack event system. Set the FTRACK_EVENT_PLUGIN_PATH
# to pick up the default hooks if it has not already been set.
os.environ.setdefault(
    'FTRACK_EVENT_PLUGIN_PATH', os.path.realpath(os.path.dirname(__file__))
)


def register(session):
    '''Mute API warnings.'''
    pass
