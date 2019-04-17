# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import ftrack_connect_pipeline_nuke
import ftrack_connect.usage

import nuke
import platform


def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    if metadata is None:
        metadata = {
            'nuke_version': nuke.NUKE_VERSION_STRING,
            'operating_system': platform.platform(),
            'ftrack_connect_pipeline_nuke_version': ftrack_connect_pipeline_nuke.__version__
        }

    ftrack_connect.usage.send_event(
        event_name, metadata
    )
