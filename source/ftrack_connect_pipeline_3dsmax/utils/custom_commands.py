# :coding: utf-8
# :copyright: Copyright (c) 2014-2020 ftrack

from pymxs import runtime as rt


def import_scene_XRef(file_path, options=None):
    '''Import a Max scene file as a Scene XRef asset.'''
    scn = rt.xrefs.addNewXRefFile(file_path)
    return scn

def re_import_scene_XRef(file_path, parent_helper_node_name):
    '''Import a Max scene file as a Scene XRef asset and parent it
    under an existing helper ftrack_object.'''
    node = rt.getNodeByName(parent_helper_node_name, exact=True)
    scn = rt.xrefs.addNewXRefFile(file_path)
    scn.parent = node
    return scn


def import_obj_XRefs(file_path, options=None):
    '''Import all the objects in a Max scene file as Object XRefs and parent
    them under an existing helper ftrack_object.'''
    x_ref_objs = rt.getMAXFileObjectNames(file_path)
    newObjs = rt.xrefs.addNewXRefObject(
        file_path, x_ref_objs, dupMtlNameAction=rt.name("autoRename")
    )
    rt.select(newObjs)
    return newObjs


def open_scene(file_path, options=None):
    '''Open a Max scene file.'''
    return rt.loadMaxFile(file_path)


def get_unique_node_name(node_name):
    '''Return a unique scene name for the given *nodeName*'''
    #TODO: check this
    # $Box01.name = uniqueName "MyRenamedBox"
    # -->"MyRenamedBox001"
    unique_node_name = None
    # Max starts naming objects from 001.
    i = 1
    node_fmt_string = node_name + '%03d'
    while True:
        unique_node_name = node_fmt_string % i
        if not rt.getNodeByName(unique_node_name, exact=True):
            return unique_node_name

        i = i + 1

    return unique_node_name


def scene_XRef_imported(ftrack_node):
    '''Check if a Scene XRef exists under the ftrackAssetHelper ftrack_object.'''
    result = False
    num_scene_refs = rt.xrefs.getXRefFileCount()
    for idx in range(1, num_scene_refs):
        scene_ref = rt.xrefs.getXrefFile(idx)
        if scene_ref.parent.Name == ftrack_node.Name:
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


def get_current_scene_objects():
    deselect_all()
    select_all()
    scene_objects = []
    for obj in save_selection():
        scene_objects.append(obj)
    deselect_all()
    return set(scene_objects)


def select_all():
    return rt.select(rt.objects)


def deselect_all():
    rt.clearSelection()


def save_selection():
    return rt.GetCurrentSelection()


def restore_selection(saved_selection):
    rt.clearSelection()
    rt.select(saved_selection)


def add_node_to_selection(node):
    '''Select Node'''
    rt.selectMore(node)


def selection_empty():
    return rt.selection.count == 0


def get_ftrack_helpers():
    helpers = []
    for obj in rt.rootScene.world.children:
        if rt.SuperClassOf(obj) == rt.helper:
            helpers.append(obj)
    return helpers


def _collect_children_nodes(n, nodes):
    for c in n.Children:
        _collect_children_nodes(c, nodes)

    nodes.append(n)


def collect_children_nodes(node):
    '''Return a list of all children of a ftrack_object.'''
    child_nodes = []
    for c in node.Children:
        _collect_children_nodes(c, child_nodes)

    return child_nodes


def delete_all_children(node):
    '''Delete all children ftrack_objects of a ftrack_object.'''
    all_children = collect_children_nodes(node)
    for node in all_children:
        rt.delete(node)
    return all_children

def delete_node(node):
    '''Delete all children ftrack_objects of a ftrack_object.'''
    rt.delete(node)


def add_all_children_to_selection(parent_node):
    '''Add all children of a ftrack_object to the current selection.'''
    current_selection = list(rt.GetCurrentSelection())
    nodes_to_select = collect_children_nodes(parent_node)
    for node in nodes_to_select:
        current_selection.append(node)
    rt.select(current_selection)

    return current_selection


def get_time_range():
    start = rt.animationRange.start
    end = rt.animationRange.end
    return (start, end)


def select_only_cameras():
    selected_cameras = []
    for obj in rt.selection:
        if rt.SuperClassOf(obj) == 'camera':
            selected_cameras.append(obj)
    return selected_cameras


def create_selection_set(set_name):
    '''Create a new selection set containing the selected ftrack_objects.'''
    rt.selectionSets[set_name] = rt.selection
