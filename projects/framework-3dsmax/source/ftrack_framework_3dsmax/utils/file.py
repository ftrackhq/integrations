# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

from pymxs import runtime as rt

from ftrack_framework_core import utils as core_utils

# File operations


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
            save_path, message = core_utils.get_save_path(
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


def reference_file(path, options=None):
    '''reference a Max scene file as a Scene XRef asset.

    Follow this link for more reference commands in max:
    https://help.autodesk.com/view/3DSMAX/2016/ENU/?guid=__files_GUID_090B28AB_5710_45BB_B324_8B6FD131A3C8_htm
    '''
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
