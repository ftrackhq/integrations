# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import os

# This is faster than glob and walk found in:
# https://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory


def fast_scandir(dirname):
    subfolders = [
        _folder.path
        for _folder in os.scandir(dirname)
        if _folder.is_dir() and not _folder.name.startswith("__")
    ]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders
