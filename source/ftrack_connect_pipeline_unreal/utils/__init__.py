# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
from functools import wraps

import unreal


def run_in_main_thread(f):
    '''Make sure a function runs in the main Unreal thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        # Multithreading is disabled for Unreal integration
        return f(*args, **kwargs)

    return decorated


def get_all_sequences(as_names=True):
    '''
    Returns a list of all sequence assets used in level. If *as_names* is True, the asset name
    will be returned instead of the asset itself.
    '''
    result = []
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in actors:
        if actor.static_class() == unreal.LevelSequenceActor.static_class():
            level_sequence = actor.load_sequence()
            value = level_sequence.get_name() if as_names else level_sequence
            if value not in result:
                result.append(value)
            break
    return result


from ftrack_connect_pipeline_unreal.utils.bootstrap import *
from ftrack_connect_pipeline_unreal.utils.node import *
from ftrack_connect_pipeline_unreal.utils.file import *
from ftrack_connect_pipeline_unreal.utils.asset import *
from ftrack_connect_pipeline_unreal.utils.project import *
