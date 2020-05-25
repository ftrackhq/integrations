# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd
from ftrack_connect_pipeline_maya.constants import asset as asset_const

def get_current_scene_objects():
    return set(cmd.ls(l=True))

def get_ftrack_nodes():
    return cmd.ls(type=asset_const.FTRACK_PLUGIN_TYPE)