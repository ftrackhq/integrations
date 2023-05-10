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


from ftrack_connect_pipeline_unreal.utils.bootstrap import *
from ftrack_connect_pipeline_unreal.utils.node import *
from ftrack_connect_pipeline_unreal.utils.file import *
from ftrack_connect_pipeline_unreal.utils.asset import *
from ftrack_connect_pipeline_unreal.utils.project import *
from ftrack_connect_pipeline_unreal.utils.sequence import *
