# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import clique
import tempfile
import logging

logger = logging.getLogger(__name__)


def find_image_sequence(file_path):
    '''Try to find a continuous image sequence in the *file_path*, supplied either as
    an explicit single file within the sequence or a folder. Will return the clique
    parsable expression.
    '''

    is_dir = False
    if not file_path or not os.path.exists(os.path.dirname(file_path)):
        return None

    if os.path.isdir(file_path):
        is_dir = True
        folder_path = file_path
    else:
        folder_path = os.path.dirname(file_path)
    # Search folder for images sequence
    collections, remainder = clique.assemble(
        os.listdir(folder_path), minimum_items=1
    )
    if not collections:
        return None

    if is_dir:
        return os.path.join(folder_path, collections[0].format())
    for collection in collections:
        if collection.match(os.path.basename(file_path)):
            return os.path.join(folder_path, collection.format())

    return None


def get_temp_path(filename_extension=None):
    '''Calculate and return a Connect temporary path,
    appending *filename_extension* if supplied.'''

    result = os.path.join(
        tempfile.gettempdir(),
        'ftrack-connect',
        'ftrack',
        '{}{}'.format(
            os.path.basename(tempfile.NamedTemporaryFile().name),
            f'.{filename_extension.split(".")[-1]}'
            if filename_extension
            else '',
        ),
    )
    if not os.path.exists(os.path.dirname(result)):
        os.makedirs(os.path.dirname(result))

    return result


def check_image_sequence(path):
    '''Check if the image sequence pointed out by *path* exists, returns metadata
    about the sequence if it does, raises an exception otherwise.'''
    directory, basename = os.path.split(path)

    p_pos = basename.find('%')
    d_pos = basename.find('d', p_pos)
    exp = basename[p_pos : d_pos + 1]

    padding = 0
    if d_pos > p_pos + 2:
        # %04d expression
        padding = int(basename[p_pos + 1 : d_pos])

    ws_pos = basename.rfind(' ')
    dash_pos = basename.find('-', ws_pos)

    prefix = basename[:p_pos]
    suffix = basename[d_pos + 1 : ws_pos]

    start = int(basename[ws_pos + 2 : dash_pos])
    end = int(basename[dash_pos + 1 : -1])

    if padding == 0:
        # No padding, calculate padding from start and end
        padding = len(str(end))

    logger.debug(
        f'Looking for frames {start}>{end} in directory {directory} starting '
        f'with {prefix}, ending with {suffix} (padding: {padding})'
    )

    for frame in range(start, end + 1):
        filename = f'{prefix}{exp % frame}{suffix}'
        test_path = os.path.join(directory, filename)
        if not os.path.exists(test_path):
            raise Exception(
                f'Image sequence member {frame} not ' f'found @ "{test_path}"!'
            )
        logger.debug(f'Frame {frame} verified: {filename}')

    return {
        'directory': directory,
        'prefix': prefix,
        'suffix': suffix,
        'start': start,
        'end': end,
        'padding': padding,
    }
