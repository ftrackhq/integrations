# :coding: utf-8
# :copyright: Copyright (c) 2014-{{cookiecutter.year}} ftrack
import threading
from functools import wraps
import logging

from ftrack_connect_pipeline.utils import (
    get_save_path,
)
from {{cookiecutter.package_name}}.constants import asset as asset_const

logger = logging.getLogger(__name__)


### COMMON UTILS ###


def run_in_main_thread(f):
    '''Make sure a function runs in the main {{cookiecutter.host_type_capitalized}} thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            # return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
            pass
        else:
            return f(*args, **kwargs)

    return decorated


def init_{{cookiecutter.host_type}}(context_id=None, session=None):
    '''
    Initialise timeline in {{cookiecutter.host_type_capitalized}} based on shot/asset build settings.

    :param session:
    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
    :return:
    '''
    pass


def get_main_window():
    """Return the QMainWindow for the main {{cookiecutter.host_type_capitalized}} window."""
    return None


### OBJECT OPERATIONS ###


def get_ftrack_nodes():
    # return cmds.ls(type=asset_const.FTRACK_PLUGIN_TYPE)
    pass


def get_current_scene_objects():
    '''Returns all the objects in the scene'''
    # return set(cmds.ls(l=True))
    pass


def collect_children_nodes(node):
    '''Return all the children of the given *node*'''
    # child_nodes = []
    # for child in node.Children:
    #     _collect_children_nodes(child, child_nodes)
    #
    # return child_nodes
    pass


def _collect_children_nodes(n, nodes):
    '''Private function to recursively return children of the given *nodes*'''
    # for child in n.Children:
    #     _collect_children_nodes(child, nodes)
    #
    # nodes.append(n)
    pass


def delete_all_children(node):
    '''Delete all children from the given *node*'''
    # all_children = collect_children_nodes(node)
    # for node in all_children:
    #     rt.delete(node)
    # return all_children
    pass


def node_exists(node_name):
    '''Check if node_name exist in the scene'''
    # return cmds.objExists(object_name)
    pass


def get_node(node_name):
    '''Return the Max node identified by name'''
    # return rt.getNodeByName(node_name, exact=True)
    pass


def delete_node(node):
    '''Delete the given *node*'''
    # return cmds.delete(object_name)
    pass


# (Only DCC with no live connections)
    # def get_connected_objects_from_dcc_object(dcc_object_name):
    #     '''Return all objects connected to the given *dcc_object_name*'''
    #     # Get Unique id for a node using rt.getHandleByAnim(obj) and get the node
    #     # from the unique id using rt.getAnimByHandler(id) please see the following
    #     # link for more info: https://help.autodesk.com/view/MAXDEV/2023/ENU/?guid=GUID-25211F97-E81A-4D49-AFB6-50B30894FBEB
    #     objects = []
    #     dcc_object_node = rt.getNodeByName(dcc_object_name, exact=True)
    #     if not dcc_object_node:
    #         return
    #     id_value = rt.getProperty(dcc_object_node, asset_const.ASSET_INFO_ID)
    #     for parent in rt.rootScene.world.children:
    #         children = [parent] + collect_children_nodes(parent)
    #         for obj in children:
    #             if rt.isProperty(obj, "ftrack"):
    #                 if id_value == rt.getProperty(obj, "ftrack"):
    #                     objects.append(obj)
    #     return objects


### SELECTION ###


def select_all():
    '''Select all objects from the scene'''
    # return rt.select(rt.objects)
    pass


def deselect_all():
    '''Clear the selection'''
    # rt.clearSelection()
    pass


def add_node_to_selection(node):
    '''Add the given *node* to the current selection'''
    # rt.selectMore(node)
    pass


def create_selection_set(set_name):
    '''Create a new selection set containing the current selection.'''
    # rt.selectionSets[set_name] = rt.selection
    pass


def selection_empty():
    '''Empty the current selection'''
    #return rt.selection.count == 0
    pass


def select_only_type(obj_type):
    '''Select all *obj_type* from the scene'''
    # selected_cameras = []
    # for obj in rt.selection:
    #     if rt.SuperClassOf(obj) == obj_type:
    #         selected_cameras.append(obj)
    # return selected_cameras
    pass


### FILE OPERATIONS ###


def open_file(path, options=None):
    '''Native open file function '''
    # return cmds.file(path, o=True, f=True)
    pass


def import_file(path, options=None):
    '''Native import file function '''
    # return cmds.file(path, o=True, f=True)
    pass


def save_file(save_path, context_id=None, session=None, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    # # Max has no concept of renaming a scene, always save
    # save = True
    #
    # if save_path is None:
    #     if context_id is not None and session is not None:
    #         # Attempt to find out based on context
    #         save_path, message = get_save_path(
    #             context_id, session, extension='.max', temp=temp
    #         )
    #
    #         if save_path is None:
    #             return False, message
    #     else:
    #         return (
    #             False,
    #             'No context and/or session provided to generate save path',
    #         )
    #
    # if save:
    #     rt.savemaxFile(save_path, useNewFile=True)
    #     message = 'Saved Max scene @ "{}"'.format(save_path)
    # else:
    #     raise Exception('Max scene rename not supported')
    #
    # result = save_path
    #
    # return result, message
    pass


### REFERENCES ###
# Follow this link for more reference commands in max:
# https://help.autodesk.com/view/3DSMAX/2016/ENU/?guid=__files_GUID_090B28AB_5710_45BB_B324_8B6FD131A3C8_htm


def reference_file(path, options=None):
    '''Native reference file function '''
    # return cmds.file(path, o=True, f=True)
    pass


def get_reference_node(dcc_object_name):
    '''
    Return the scene reference_node associated to the given
    *dcc_object_name*
    '''
    # dcc_object_node = rt.getNodeByName(dcc_object_name, exact=True)
    # if not dcc_object_node:
    #     return
    # component_path = asset_const.COMPONENT_PATH
    # for idx in range(1, rt.xrefs.getXRefFileCount()):
    #     reference_node = rt.xrefs.getXrefFile(idx)
    #     if reference_node.filename == component_path:
    #         return reference_node
    pass


def remove_reference_node(reference_node):
    '''Remove reference'''
    # rt.delete(reference_node)
    pass


def unload_reference_node(reference_node):
    '''Disable reference'''
    # reference_node.disabled = True
    pass


def load_reference_node(reference_node):
    '''Disable reference'''
    #reference_node.disabled = False
    pass


def update_reference_path(reference_node, component_path):
    '''Update the path of the given *reference_node* with the given
    *component_path*'''
    #reference_node.filename = component_path
    pass


### TIME OPERATIONS ###


def get_time_range():
    '''Return the start and end frame of the current scene'''
    # start = rt.animationRange.start
    # end = rt.animationRange.end
    # return (start, end)
    pass

