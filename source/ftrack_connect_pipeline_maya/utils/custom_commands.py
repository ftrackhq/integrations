# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import maya.cmds as cmd
from ftrack_connect_pipeline_maya.constants import asset as asset_const


def get_current_scene_objects():
    return set(cmd.ls(l=True))


def get_ftrack_nodes():
    return cmd.ls(type=asset_const.FTRACK_PLUGIN_TYPE)


def open_file(path, options):
    return cmd.file(path, o=True, f=True)


def import_file(path, options):
    return cmd.file(path, i=True, **options)


def reference_file(path, options):
    return cmd.file(path, r=True, **options)
