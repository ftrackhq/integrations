# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack

import os
import warnings


def prepend_path(path, key, environment):
    '''Prepend *path* to *key* in *environment*.'''
    try:
        environment[key] = os.pathsep.join([path, environment[key]])
    except KeyError:
        environment[key] = path

    return environment


def append_path(path, key, environment):
    '''Append *path* to *key* in *environment*.'''
    try:
        environment[key] = os.pathsep.join([environment[key], path])
    except KeyError:
        environment[key] = path

    return environment


# legacy
def appendPath(path, key, environment):
    '''Prepend *path* to *key* in *environment*.'''
    warnings.warn(
        "appendPath will be deprecated in upcoming version, use append_path instead",
        PendingDeprecationWarning,
    )
    return append_path(path, key, environment)


def prependPath(path, key, environment):
    '''Prepend *path* to *key* in *environment*.'''
    warnings.warn(
        "prependPath will be deprecated in upcoming version, use prepend_path instead",
        PendingDeprecationWarning,
    )
    return prepend_path(path, key, environment)
