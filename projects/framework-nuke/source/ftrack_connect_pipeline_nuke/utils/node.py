# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import nuke

from ftrack_connect_pipeline_nuke.constants import asset as asset_const


def get_unique_scene_name(current_name):
    '''
    Returns a unique name from the given *current_name*

    *current_name*: string name of an object.
    '''
    res = nuke.toNode(str(current_name))
    if res:
        i = 0
        while res:
            unique_name = current_name + str(i)
            res = nuke.toNode(str(current_name))
            i = i + 1
        return unique_name
    else:
        return current_name


def get_nodes_with_ftrack_tab():
    '''
    Returns all the nuke dcc_objects that contain an ftrack tab.
    '''
    dependencies = []
    for node in nuke.allNodes():
        if asset_const.FTRACK_PLUGIN_TYPE in node.knobs().keys():
            dependencies.append(node)
    return dependencies


def get_current_scene_objects():
    '''Get all objects in the current Nuke scene.'''
    return set(nuke.allNodes())


def get_all_write_nodes():
    '''Return all write nodes in the current Nuke scene.'''
    write_nodes = []
    for node in nuke.allNodes('Write'):
        write_nodes.append(node)
    return write_nodes


def clean_selection():
    '''Clean the current selection in Nuke.'''
    for node in nuke.selectedNodes():
        node['selected'].setValue(False)


def get_path_from_image_sequence_write_node(node_name):
    '''Extract path from the write node'''
    full_path = None
    if not node_name:
        return full_path
    node = nuke.toNode(node_name)

    if (
        not node.Class() == 'Write'
        and node.knob('file')
        and node.knob('first')
        and node.knob('last')
    ):
        return full_path

    node_file_path = node.knob('file').value()
    if node.knob('use_limit').value():
        first = int(node.knob('first').value())
        last = int(node.knob('last').value())
    else:
        first = int(nuke.root()["first_frame"].getValue())
        last = int(nuke.root()["last_frame"].getValue())
    full_path = '{} [{}-{}]'.format(node_file_path, first, last)
    return full_path
