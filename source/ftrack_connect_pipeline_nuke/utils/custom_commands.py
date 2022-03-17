# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import re
import os
import glob
import traceback

import logging

import nuke
import nukescripts

from ftrack_connect_pipeline_nuke.constants import asset as asset_const

logger = logging.getLogger(__name__)


def get_sequence_fist_last_frame(path):
    '''
    Returns first and last frame from the given *path*
    '''
    try:
        if '%V' in path:
            path = path.replace('%V', 'left')
        has_match = re.search('#+', path)
        if has_match:
            path = path[: has_match.start(0)] + '*' + path[has_match.end(0) :]

        nuke_format_match = re.search('%\d+d', path)
        if nuke_format_match:
            path = (
                path[: nuke_format_match.start(0)]
                + '*'
                + path[nuke_format_match.end(0) :]
            )

        file_extension = os.path.splitext(path)[1].replace('.', '\.')
        files = sorted(glob.glob(path))
        regexp = '(\d+){} '.format(file_extension)
        first = int(re.findall(regexp, files[0])[0])
        last = int(re.findall(regexp, files[-1])[0])
    except:
        traceback.print_exc(file=sys.stdout)
        first = 1
        last = 1
    return first, last


def sequence_exists(file_path):
    seq = re.compile('(\w+).+(\%\d+d).(\w+)')
    logger.debug('searching for {}'.format(file_path))

    frames = glob.glob(file_path)
    n_files = len(frames)
    logger.debug('Sequence frames {}'.format(n_files))
    first, last = get_sequence_fist_last_frame(file_path)
    total_frames = (last - first) + 1
    logger.debug('Sequence lenght {}'.format(total_frames))
    if n_files != total_frames:
        return False

    return True


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
    Returns all the nuke ftrack_objects that contain an ftrack tab.
    '''
    dependencies = []
    for node in nuke.allNodes():
        if asset_const.FTRACK_PLUGIN_TYPE in node.knobs().keys():
            dependencies.append(node)
    return dependencies


def reference_script(path, options=None):
    '''
    Create LiveGroup from the givem *path*
    '''
    node = nuke.createNode(
        'LiveGroup', 'published true file {}'.format(path), inpanel=False
    )
    return node


def open_script(path, options=None):
    '''
    Open nuke scene from the given *path*
    '''
    result = nuke.scriptOpen(path)
    return result


def import_script(path, options=None):
    '''
    Import the scene from the given *path*
    '''
    return nuke.nodePaste(path)


def get_current_scene_objects():
    return set(nuke.allNodes())


def get_all_write_nodes():
    write_nodes = []
    for node in nuke.allNodes('Write'):
        write_nodes.append(node)
    return write_nodes


def cleanSelection():
    for node in nuke.selectedNodes():
        node['selected'].setValue(False)


def save_snapshot(filename, context_id, session):
    '''Save scene locally, with the next version number based on latest version
    in ftrack.'''
    snapshot_path_base = os.environ.get('FTRACK_SNAPSHOT_PATH')

    context = session.query('Context where id={}'.format(context_id)).first()

    if context is None:
        raise Exception(
            'Could not save snapshot - unknown context: {}!'.format(context_id)
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
        snapshot_path = os.sep.join(
            [snapshot_path_base] + structure_names + ['work']
        )
    else:
        # Try to query location system (future)
        try:
            location = session.pick_location()
            snapshot_path = location.get_filesystem_path(context)
        except:
            # Ok, use default location
            snapshot_path_base = os.path.join(
                os.path.expanduser('~'),
                'Documents',
                'ftrack_work_path',
            )
            # Build path down to context
            snapshot_path = os.sep.join([snapshot_path_base] + structure_names)

    if snapshot_path is not None:
        if not os.path.exists(snapshot_path):
            os.makedirs(snapshot_path)
        if not os.path.exists(snapshot_path):
            return (
                None,
                'Could not create snapshot directory: {}!'.format(
                    snapshot_path
                ),
            )
        # Make sure we do not overwrite existing work done
        snapshot_path = os.path.join(
            snapshot_path, '%s_v%03d.nk' % (filename, next_version_number)
        )

        while os.path.exists(snapshot_path):
            next_version_number += 1
            snapshot_path = os.path.join(
                os.path.dirname(snapshot_path),
                '%s_v%03d.nk' % (filename, next_version_number),
            )

        # Save Maya scene to this path
        nuke.scriptSaveAs(snapshot_path, overwrite=1)
        message = 'Saved Nuke script @ "{}"'.format(snapshot_path)
        result = snapshot_path
    else:
        message = 'Could not evaluate local snapshot path!'

    return result, message
