# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack
import os

from Qt import QtWidgets, QtCompat

import maya.OpenMayaUI as OpenMayaUI

import maya.cmds as cmds

from ftrack_connect_pipeline_maya.constants import asset as asset_const


def get_current_scene_objects():
    return set(cmds.ls(l=True))


def get_ftrack_nodes():
    return cmds.ls(type=asset_const.FTRACK_PLUGIN_TYPE)


def open_file(path, options):
    return cmds.file(path, o=True, f=True)


def import_file(path, options):
    return cmds.file(path, i=True, **options)


def reference_file(path, options):
    return cmds.file(path, r=True, **options)


def remove_reference_node(referenceNode):
    return cmds.file(rfn=referenceNode, rr=True)


def getReferenceNode(assetLink):
    '''Return the references ftrack_objects for the given *assetLink*'''
    res = ''
    try:
        res = cmds.referenceQuery(assetLink, referenceNode=True)
    except:
        children = cmds.listRelatives(assetLink, children=True)

        if children:
            for child in children:
                try:
                    res = cmds.referenceQuery(child, referenceNode=True)
                    break

                except:
                    pass
        else:
            return None
    if res == '':
        print('Could not find reference ftrack_object')
        return None
    else:
        return res


def get_maya_window():
    """Return the QMainWindow for the main Maya window."""

    winptr = OpenMayaUI.MQtUtil.mainWindow()
    if winptr is None:
        raise RuntimeError('No Maya window found.')
    window = QtCompat.wrapInstance(int(winptr))
    assert isinstance(window, QtWidgets.QMainWindow)
    return window


def save_snapshot(filename, context_id, session, ask_load=False):
    '''Save scene locally, with the next version number based on latest version
    in ftrack.'''
    snapshot_path_base = os.environ.get('FTRACK_SNAPSHOT_PATH')

    context = session.query('Context where id={}'.format(context_id)).first()

    if context is None:
        raise Exception(
            'Could not save snapshot - unknown context by ID: {}!'.format(
                context_id
            )
        )

    if filename is None:
        # TODO: use task type <> asset type mappings
        filename = context['type']['name']  # Modeling, compositing...

    result = False
    message = None

    structure_names = [context['project']['name']] + [
        item['name'] for item in context['link'][1:]
    ]

    # Find latest version number
    next_version_number = 1
    latest_asset_version = session.query(
        'AssetVersion where '
        'task.id={} and is_latest_version=true'.format(context_id)
    ).first()
    if latest_asset_version:
        next_version_number = latest_asset_version['version'] + 1

    if snapshot_path_base:
        # Build path down to context
        work_path = os.sep.join(
            [snapshot_path_base] + structure_names + ['work']
        )
    else:
        # Try to query location system (future)
        try:
            location = session.pick_location()
            work_path = location.get_filesystem_path(context)
        except:
            # Ok, use default location
            snapshot_path_base = os.path.join(
                os.path.expanduser('~'),
                'Documents',
                'ftrack_work_path',
            )
            # Build path down to context
            work_path = os.sep.join([snapshot_path_base] + structure_names)

    if work_path is not None:
        if not os.path.exists(work_path):
            os.makedirs(work_path)
        if not os.path.exists(work_path):
            return (
                None,
                'Could not create work directory: {}!'.format(work_path),
            )
        # Make sure we do not overwrite existing work done
        work_path = os.path.join(
            work_path, '%s_v%03d' % (filename, next_version_number)
        )
        do_load = False
        if ask_load and os.path.exists(work_path):
            # Attempt to ask user
            try:
                from ftrack_connect_pipeline_qt.ui.utility.widget.dialog import (
                    Dialog,
                )

                dlg = Dialog(
                    None,
                    title='ftrack Maya Save',
                    question='Load existing local snapshot({})?'.format(
                        os.path.basename(work_path)
                    ),
                    prompt=True,
                )
                if dlg.exec_():
                    do_load = True

            except ImportError:
                pass
        if not do_load:
            while os.path.exists(work_path):
                next_version_number += 1
                work_path = os.path.join(
                    work_path,
                    '%s_v%03d' % (filename, next_version_number),
                )

            # Save Maya scene to this path
            cmds.file(rename=work_path)
            cmds.file(save=True)
            message = 'Saved Maya scene @ "{}"'.format(work_path)
            result = work_path
        else:
            cmds.file(work_path, open=True, f=True)
            message = 'Opened Maya scene @ "{}"'.format(work_path)
            result = work_path
    else:
        message = 'Could not evaluate local snapshot path!'

    return result, message
