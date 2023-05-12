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


from framework_unreal.utils.bootstrap import *
from framework_unreal.utils.node import *
from framework_unreal.utils.file import *
from framework_unreal.utils.asset import *
from framework_unreal.utils.project import *
from framework_unreal.utils.sequence import *
