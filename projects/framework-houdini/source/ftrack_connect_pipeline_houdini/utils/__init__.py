# :coding: utf-8
# :copyright: Copyright (c) 2014-2023 ftrack
import threading
from functools import wraps

import hdefereval


def run_in_main_thread(f):
    '''Make sure a function runs in the main Maya thread.'''

    @wraps(f)
    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return hdefereval.executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated


from ftrack_connect_pipeline_houdini.utils.bootstrap import *
from ftrack_connect_pipeline_houdini.utils.file import *
from ftrack_connect_pipeline_houdini.utils.node import *
