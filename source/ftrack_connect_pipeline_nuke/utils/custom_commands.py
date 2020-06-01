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
    try:
        if '%V' in path:
            path = path.replace('%V', 'left')
        hashMatch = re.search('#+', path)
        if hashMatch:
            path = path[:hashMatch.start(0)] + '*' + path[hashMatch.end(0):]

        nukeFormatMatch = re.search('%\d+d', path)
        if nukeFormatMatch:
            path = (
                path[:nukeFormatMatch.start(0)] + '*' +
                path[nukeFormatMatch.end(0):]
            )

        fileExtension = os.path.splitext(path)[1].replace('.', '\.')
        files = sorted(glob.glob(path))
        regexp = '(\d+)' + fileExtension + ''
        first = int(re.findall(regexp, files[0])[0])
        last = int(re.findall(regexp, files[-1])[0])
    except:
        traceback.print_exc(file=sys.stdout)
        first = 1
        last = 1
    return first, last


def sequence_exists(filepath):
    seq = re.compile('(\w+).+(\%\d+d).(\w+)')
    logger.info('searching for {}'.format(filepath))

    frames = glob.glob(filepath)
    nfiles = len(frames)
    logger.info('Sequence frames {}'.format(nfiles))
    first, last = get_sequence_fist_last_frame(filepath)
    total_frames = (last - first) + 1
    logger.info('Sequence lenght {}'.format(total_frames))
    if nfiles != total_frames:
        return False

    return True


def get_unique_scene_name(current_name):
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
    dependencies = []
    for node in nuke.allNodes():
        if asset_const.FTRACK_PLUGIN_TYPE in node.knobs().keys():
            dependencies.append(node)
    return dependencies