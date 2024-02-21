# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os
import clique
import tempfile


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
