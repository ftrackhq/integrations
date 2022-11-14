# :coding: utf-8
# :copyright: Copyright (c) 2022 ftrack
import logging
import threading
from functools import wraps

import shiboken2

from pymxs import runtime as rt

from Qt import QtWidgets

from ftrack_connect_pipeline.utils import (
    get_save_path,
)
from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const

logger = logging.getLogger(__name__)


### COMMON UTILS ###

def run_in_main_thread(f):
    '''Make sure a function runs in the main Max thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            # return maya_utils.executeInMainThreadWithResult(f, *args, **kwargs)
            pass
        else:
            return f(*args, **kwargs)

    return decorated


def init_max(context_id=None, session=None):
    '''
    Initialise timeline in Max based on shot/asset build settings.

    :param session:
    :param context_id: If provided, the timeline data should be fetched this context instead of environment variables.
    :param session: The session required to query from *context_id*.
    :return:
    '''
    # TODO: To be implemented
    pass


def get_main_window():
    '''Return the QMainWindow for the main Max window.'''
    main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
    main_window = shiboken2.wrapInstance(
        shiboken2.getCppPointer(main_window_qwdgt)[0], QtWidgets.QMainWindow
    )
    return main_window


### OBJECT OPERATIONS ###

def get_ftrack_nodes():
    '''Returns all DCC objects in the scene'''
    dcc_objects = []
    for obj in rt.rootScene.world.children:
        if rt.SuperClassOf(obj) == rt.helper:
            if obj.ClassID == asset_const.FTRACK_PLUGIN_ID:
                dcc_objects.append(obj)
    return dcc_objects


def get_current_scene_objects():
    '''Returns all the objects in the scene'''
    deselect_all()
    select_all()
    scene_objects = []
    for obj in save_selection():
        scene_objects.append(obj)
    deselect_all()
    return set(scene_objects)


def collect_children_nodes(node):
    '''Return all the children of the given *node*'''
    child_nodes = []
    for child in node.Children:
        _collect_children_nodes(child, child_nodes)

    return child_nodes


def _collect_children_nodes(n, nodes):
    '''Private function to recursively return children of the given *nodes*'''
    for child in n.Children:
        _collect_children_nodes(child, nodes)

    nodes.append(n)


def delete_all_children(node):
    '''Delete all children from the given *node*'''
    all_children = collect_children_nodes(node)
    for node in all_children:
        rt.delete(node)
    return all_children


def node_exists(node_name):
    '''Check if node_name exist in the scene'''
    if not rt.getNodeByName(node_name, exact=True):
        return False
    return True


def delete_node(node):
    ''' Delete the given *node*'''
    rt.delete(node)


### SELECTION ###

def select_all():
    '''Select all objects from the scene'''
    return rt.select(rt.objects)


def deselect_all():
    '''Clear the selection'''
    rt.clearSelection()


def save_selection():
    '''Save the current selection'''
    return rt.GetCurrentSelection()


def restore_selection(saved_selection):
    '''Clean the current selection and select the given *saved_selection*'''
    rt.clearSelection()
    rt.select(saved_selection)


def add_node_to_selection(node):
    '''Add the given *node* to the current selection'''
    rt.selectMore(node)


def selection_empty():
    '''Empty the current selection'''
    return rt.selection.count == 0


def add_all_children_to_selection(parent_node):
    '''Add all children of the given *parent_node* to the current selection.'''
    current_selection = list(rt.GetCurrentSelection())
    nodes_to_select = collect_children_nodes(parent_node)
    for node in nodes_to_select:
        current_selection.append(node)
    rt.select(current_selection)

    return current_selection


def create_selection_set(set_name):
    '''Create a new selection set containing the current selection.'''
    rt.selectionSets[set_name] = rt.selection


def select_only_cameras():
    ''' Select all cameras from the scene'''
    selected_cameras = []
    for obj in rt.selection:
        if rt.SuperClassOf(obj) == 'camera':
            selected_cameras.append(obj)
    return selected_cameras


### FILE OPERATIONS ###

def open_file(path, options=None):
    '''Native open file function'''
    return rt.loadMaxFile(path)


def import_scene_XRef(file_path, options=None):
    '''Import a Max scene file as a Scene XRef asset.'''
    scene_node = rt.xrefs.addNewXRefFile(file_path)
    return scene_node


def re_import_scene_XRef(file_path, parent_helper_node_name):
    '''Import a Max scene file as a Scene XRef asset and parent it
    under the given *parent_helper_node_name*.'''
    node = rt.getNodeByName(parent_helper_node_name, exact=True)
    scene_node = rt.xrefs.addNewXRefFile(file_path)
    scene_node.parent = node
    return scene_node


def import_obj_XRefs(file_path, options=None):
    '''Import all the objects in a Max scene file as Object XRefs'''
    x_ref_objs = rt.getMAXFileObjectNames(file_path)
    newObjs = rt.xrefs.addNewXRefObject(
        file_path, x_ref_objs, dupMtlNameAction=rt.name("autoRename")
    )
    rt.select(newObjs)
    return newObjs


def scene_XRef_imported(node):
    '''Check if a Scene XRef exists under the given *node* '''
    result = False
    num_scene_refs = rt.xrefs.getXRefFileCount()
    for idx in range(1, num_scene_refs):
        scene_ref = rt.xrefs.getXrefFile(idx)
        if scene_ref.parent.Name == node.Name:
            result = True
    return result


def merge_max_file(file_path, options=None):
    '''Import a Max scene into the current scene.'''
    return rt.mergemaxfile(
        file_path,
        rt.name("autoRenameDups"),
        rt.name("neverReparent"),
        rt.name("select")
    )


def save_file(save_path, context_id=None, session=None, temp=True, save=True):
    '''Save scene locally in temp or with the next version number based on latest version
    in ftrack.'''

    # Max has no concept of renaming a scene, always save
    save = True

    if save_path is None:
        if context_id is not None and session is not None:
            # Attempt to find out based on context
            save_path, message = get_save_path(
                context_id, session, extension='.max', temp=temp
            )

            if save_path is None:
                return (False, message)
        else:
            return (
                False,
                'No context and/or session provided to generate save path',
            )

    if save:
        rt.savemaxFile(save_path, useNewFile=True)
        message = 'Saved Max scene @ "{}"'.format(save_path)
    else:
        raise Exception('Max scene rename not supported')

    result = save_path

    return result, message


### REFERENCES ###

def remove_reference_node(referenceNode):
    # return cmds.file(rfn=referenceNode, rr=True)
    # TODO: To be implemented
    pass


def unload_reference_node(referenceNode):
    # return cmds.file(unloadReference=referenceNode)
    # TODO: To be implemented
    pass


def load_reference_node(referenceNode):
    # return cmds.file(loadReference=referenceNode)
    # TODO: To be implemented
    pass


def getReferenceNode(assetLink):
    '''Return the references dcc_objects for the given *assetLink*'''
    # TODO: To be implemented
    pass


### TIME OPERATIONS ###

def get_time_range():
    ''' Return the start and end frame of the current scene'''
    start = rt.animationRange.start
    end = rt.animationRange.end
    return (start, end)

