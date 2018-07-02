# :coding: utf-8
# :copyright: Copyright (c) 2018 ftrack

import nuke

import ftrack_connect.usage
import ftrack_connect_nuke_studio_beta


def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    if metadata is None:
        metadata = {
            'nuke_studio_beta_version':
                nuke.NUKE_VERSION_STRING,
            'ftrack_connect_nuke_studio_beta_version':
                ftrack_connect_nuke_studio_beta.__version__
        }

    ftrack_connect.usage.send_event(
        event_name, metadata
    )
