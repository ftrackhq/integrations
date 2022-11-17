# :coding: utf-8
# :copyright: Copyright (c) 2022 ftrack
import logging
import threading
from functools import wraps
import os
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
            raise Exception(
                '3DS Max does not support multithreading, please revisit DCC implementation!'
            )
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
    fstart = fend = fps = None
    if context_id:
        assert session is not None, 'Session not provided'
        context = session.query(
            'Context where id={}'.format(context_id)
        ).first()
        if context is None:
            logger.error(
                'Cannot initialize Maya timeline - no such context: {}'.format(
                    context_id
                )
            )
            return
        shot = None
        if context.entity_type == 'Shot':
            shot = context
        elif context.entity_type == 'Task':
            parent = context['parent']
            if parent.entity_type == 'Shot':
                shot = parent
        if not shot:
            logger.warning(
                'Cannot initialize Maya timeline - no shot related to context: {}'.format(
                    context_id
                )
            )
            return
        elif (
            not 'fstart' in shot['custom_attributes']
            or not 'fend' in shot['custom_attributes']
        ):
            logger.warning(
                'Cannot initialize Maya timeline - no fstart or fend shot custom attributes available'.format()
            )
            return
        if 'fstart' in shot['custom_attributes']:
            fstart = float(shot['custom_attributes']['fstart'])
        if 'fend' in shot['custom_attributes']:
            fend = float(shot['custom_attributes']['fend'])
        if 'fps' in shot['custom_attributes']:
            fps = float(shot['custom_attributes']['fps'])
    else:
        # Set default values from environments.
        if 'FS' in os.environ and len(os.environ['FS'] or '') > 0:
            fstart = float(os.environ.get('FS', 0))
        if 'FE' in os.environ and len(os.environ['FE'] or '') > 0:
            fend = float(os.environ.get('FE', 100))
        if 'FPS' in os.environ and len(os.environ['FPS'] or '') > 0:
            fps = float(os.environ['FPS'])

    if fstart is not None and fend is not None:
        logger.info('Setting animation range : {}-{}'.format(fstart, fend))
        rt.animationRange = rt.interval(fstart, fend)


def get_main_window():
    '''Return the QMainWindow for the main Max window.'''
    main_window_qwdgt = QtWidgets.QWidget.find(rt.windows.getMAXHWND())
    main_window = shiboken2.wrapInstance(
        shiboken2.getCppPointer(main_window_qwdgt)[0], QtWidgets.QMainWindow
    )
    return main_window


### OBJECT OPERATIONS ###


def get_ftrack_nodes():
    '''Returns all DCC nodes in the scene'''
    dcc_objects = []
    for obj in rt.rootScene.world.children:
        if rt.SuperClassOf(obj) == rt.helper:
            if tuple(obj.ClassID) == asset_const.FTRACK_PLUGIN_ID:
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


def get_node(node_name):
    '''Return the Max node identified by name'''
    return rt.getNodeByName(node_name, exact=True)


def delete_node(node):
    '''Delete the given *node*'''
    rt.delete(node)


def get_connected_objects_from_dcc_object(dcc_object_name):
    '''Return all objects connected to the given *dcc_object_name*'''
    # Get Unique id for a node using rt.getHandleByAnim(obj) and get the node
    # from the unique id using rt.getAnimByHandler(id) please see the following
    # link for more info: https://help.autodesk.com/view/MAXDEV/2023/ENU/?guid=GUID-25211F97-E81A-4D49-AFB6-50B30894FBEB
    objects = []
    dcc_object_node = rt.getNodeByName(dcc_object_name, exact=True)
    if not dcc_object_node:
        return
    id_value = rt.getProperty(dcc_object_node, asset_const.ASSET_INFO_ID)
    for parent in rt.rootScene.world.children:
        children = [parent] + collect_children_nodes(parent)
        for obj in children:
            if rt.isProperty(obj, "ftrack"):
                if id_value == rt.getProperty(obj, "ftrack"):
                    objects.append(obj)
    return objects


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
    '''Select all cameras from the scene'''
    selected_cameras = []
    for obj in rt.selection:
        if rt.SuperClassOf(obj) == 'camera':
            selected_cameras.append(obj)
    return selected_cameras


### FILE OPERATIONS ###


def open_file(path, options=None):
    '''Native open file function'''
    return rt.loadMaxFile(path)


def import_file(file_path, options=None):
    '''Import a Max scene into the current scene.'''
    return rt.mergemaxfile(
        file_path,
        rt.name("autoRenameDups"),
        rt.name("neverReparent"),
        rt.name("select"),
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
                return False, message
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
# Follow this link for more reference commands in max:
# https://help.autodesk.com/view/3DSMAX/2016/ENU/?guid=__files_GUID_090B28AB_5710_45BB_B324_8B6FD131A3C8_htm


def reference_file(path, options=None):
    '''reference a Max scene file as a Scene XRef asset.'''
    # TODO: feature implement options: XRefObject true to use the object xref
    #  reference mode wich will be something along the following lines:
    #  x_ref_objs = rt.getMAXFileObjectNames(file_path)
    #     newObjs = rt.xrefs.addNewXRefObject(
    #         file_path, x_ref_objs, dupMtlNameAction=rt.name("autoRename")
    #     )
    #     rt.select(newObjs)
    #     return newObjs
    scene_node = rt.xrefs.addNewXRefFile(path)
    return scene_node


def get_reference_node(dcc_object_name):
    '''
    Return the scene reference_node associated to the given
    *dcc_object_name*
    '''
    dcc_object_node = rt.getNodeByName(dcc_object_name, exact=True)
    if not dcc_object_node:
        return
    component_path = asset_const.COMPONENT_PATH
    for idx in range(1, rt.xrefs.getXRefFileCount()):
        reference_node = rt.xrefs.getXrefFile(idx)
        if reference_node.filename == component_path:
            return reference_node


def remove_reference_node(reference_node):
    '''Remove reference'''
    rt.delete(reference_node)


def unload_reference_node(reference_node):
    '''Disable reference'''
    reference_node.disabled = True


def load_reference_node(reference_node):
    '''Disable reference'''
    reference_node.disabled = False


def update_reference_path(reference_node, component_path):
    '''Update the path of the given *reference_node* with the given
    *component_path*'''
    reference_node.filename = component_path


### TIME OPERATIONS ###


def get_time_range():
    '''Return the start and end frame of the current scene'''
    start = rt.animationRange.start
    end = rt.animationRange.end
    return (start, end)
