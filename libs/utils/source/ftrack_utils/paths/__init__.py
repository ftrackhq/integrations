# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import clique


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


def find_files(file_path, file_filter=None, directory_filter=None):
    '''
    Returns(generator) the files or directories in the given *file_path*. If *file_filter*
    is supplied, only files matching the filter will be returned. If *directory_filter*
    is supplied, only directories matching the filter will be returned. If not filter
    is returned, all files is returned.
    '''

    if not os.path.isdir(file_path):
        raise Exception(
            'Path does not exist or is not a directory: {0}'.format(file_path)
        )
    for root, dirs, files in os.walk(file_path):
        if file_filter:
            for f in files:
                if file_filter(f):
                    yield os.path.join(root, f)
        if directory_filter:
            for d in dirs:
                if directory_filter(d):
                    yield os.path.join(root, d)
        if not file_filter and not directory_filter:
            yield os.path.join(root, f)
