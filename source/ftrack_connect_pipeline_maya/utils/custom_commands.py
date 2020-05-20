# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd

def get_current_scene_objects():
    return set(cmd.ls())

def get_ftrack_nodes():
    return cmd.ls(type='ftrackAssetNode')