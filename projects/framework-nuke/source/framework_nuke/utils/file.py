# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import logging
import os
import re
import glob
import sys
import traceback

import nuke

from framework_core.utils import (
    get_save_path,
)

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


def save_file(context_id, session, temp=True):
    '''Save script locally, with the next version number based on latest version
    in ftrack.'''

    save_path, message = get_save_path(
        context_id, session, extension='.nk', temp=temp
    )

    if save_path is None:
        return False, message

    nuke.scriptSaveAs(save_path, overwrite=1)
    message = 'Saved Nuke script @ "{}"'.format(save_path)
    result = save_path

    return result, message
