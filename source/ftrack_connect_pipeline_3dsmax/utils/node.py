# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from pymxs import runtime as rt

from ftrack_connect_pipeline_3dsmax.constants import asset as asset_const


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


# Selection


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
    '''Create a new selection set containing the current selection named *set_name*'''
    rt.selectionSets[set_name] = rt.selection


def select_only_cameras():
    '''Select all cameras from the scene'''
    selected_cameras = []
    for obj in rt.selection:
        if rt.SuperClassOf(obj) == 'camera':
            selected_cameras.append(obj)
    return selected_cameras


def get_reference_node(dcc_object_name):
    '''
    Return the scene reference_node associated to the given
    *dcc_object_name*
    '''
    dcc_object_node = rt.getNodeByName(dcc_object_name, exact=True)
    if not dcc_object_node:
        return None
    component_path = rt.getProperty(
        dcc_object_node, asset_const.COMPONENT_PATH
    )
    for idx in range(1, rt.xrefs.getXRefFileCount() + 1):
        reference_node = rt.xrefs.getXrefFile(idx)
        if reference_node.filename == component_path:
            return reference_node
    return None


def remove_reference_node(reference_node):
    '''Remove reference from the scene named *reference_node*'''
    rt.delete(reference_node)


def unload_reference_node(reference_node):
    '''Disable reference named *reference_node* in the scene'''
    reference_node.disabled = True


def load_reference_node(reference_node):
    '''Enable reference named *reference_node* in the scene'''
    reference_node.disabled = False


def update_reference_path(reference_node, component_path):
    '''Update the path of the given *reference_node* with the given
    *component_path*'''
    reference_node.filename = component_path
