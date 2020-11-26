# :coding: utf-8
# :copyright: Copyright (c) 2017 ftrack

import ftrack_connect_pipeline_maya
import ftrack_connect.usage

import maya.cmds as cmds

def send_event(event_name, metadata=None):
    '''Send usage information to server.'''

    if metadata is None:
        metadata = {
            'maya_version': cmds.about(v=True),
            'operating_system': cmds.about(os=True),
            'ftrack_connect_pipeline_maya_version': ftrack_connect_pipeline_maya.__version__
        }

    ftrack_connect.usage.send_event(
        event_name, metadata
    )
