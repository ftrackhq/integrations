# :coding: utf-8
# :copyright: Copyright (c) 2019 ftrack

import sys
import re
import os
import glob
import traceback

import logging

import nuke

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
            path = path[:has_match.start(0)] + '*' + path[has_match.end(0):]

        nuke_format_match = re.search('%\d+d', path)
        if nuke_format_match:
            path = (
                path[:nuke_format_match.start(0)] + '*' +
                path[nuke_format_match.end(0):]
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
    logger.info('searching for {}'.format(file_path))

    frames = glob.glob(file_path)
    n_files = len(frames)
    logger.info('Sequence frames {}'.format(n_files))
    first, last = get_sequence_fist_last_frame(file_path)
    total_frames = (last - first) + 1
    logger.info('Sequence lenght {}'.format(total_frames))
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
    Returns all the nuke nodes that contain an ftrack tab.
    '''
    dependencies = []
    for node in nuke.allNodes():
        if asset_const.FTRACK_PLUGIN_TYPE in node.knobs().keys():
            dependencies.append(node)
    return dependencies


def reference_scene(path):
    '''
    Create LiveGroup from the givem *path*
    '''
    node = nuke.createNode(
        'LiveGroup', 'published true file {}'.format(path), inpanel=False
    )
    # TODO: activate this in case any problem with the live group. Not sure if
    #  published should be activated or not, but we have to set it to true on
    #  creation time to avoid the override message
    # node["published"].fromScript("0")
    # node.reload()
    return node
