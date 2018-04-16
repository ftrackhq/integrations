# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import nuke

import ftrack_connect.usage
import ftrack_connect_nuke_studio


def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    if metadata is None:
        metadata = {
            'nuke_studio_version':
                nuke.NUKE_VERSION_STRING,
            'ftrack_connect_nuke_studio_version':
                ftrack_connect_nuke_studio.__version__
        }

    ftrack_connect.usage.send_event(
        event_name, metadata
    )
