# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os

# This is faster than glob and walk found in:
# https://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory


def fast_scandir(dirname):
    subfolders = [
        f.path
        for f in os.scandir(dirname)
        if f.is_dir() and not f.name.startswith("__")
    ]
    for dirname in list(subfolders):
        subfolders.extend(fast_scandir(dirname))
    return subfolders
