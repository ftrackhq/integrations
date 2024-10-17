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


def get_temp_path(filename_extension=None, is_directory=False):
    '''Calculate and return a Connect temporary path,
    appending *filename_extension* if supplied.'''

    base_temp_dir = os.path.join(
        tempfile.gettempdir(), 'ftrack-connect', 'ftrack'
    )

    # Ensure the base temporary directory exists
    if not os.path.exists(base_temp_dir):
        os.makedirs(base_temp_dir)

    if is_directory:
        # Create a temporary directory
        result = tempfile.mkdtemp(dir=base_temp_dir)
    else:
        # Create a temporary file and get its path
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, dir=base_temp_dir
        )
        # NamedTemporaryFile keeps a handle open to the file. We have to close that explicitly
        # if we're not using it as a contextmanger.
        temp_file.close()

        result = temp_file.name

        # If a filename extension is provided, append it to the file name
        if filename_extension:
            result_with_extension = (
                f'{result}.{filename_extension.split(".")[-1]}'
            )
            os.rename(result, result_with_extension)
            result = result_with_extension

    return result
