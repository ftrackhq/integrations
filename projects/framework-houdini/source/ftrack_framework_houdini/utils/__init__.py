# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import threading

from hdefereval import executeInMainThreadWithResult


# Show widget in Houdini
def dock_houdini_right(widget):
    '''Show *widget* as a floating window in Houdini.

    Docking into a Houdini Python Panel is intentionally not enabled: no other
    DCC integration docks (Maya/Nuke float, Blender passes no dock function),
    and embedding the dialog into a Python Panel segfaults on Qt6 / Houdini 21
    (the ftrack_qt StyledDialog is a top-level QDialog flagged WA_DeleteOnClose
    and WindowStaysOnTopHint). Shown floating instead, like the other DCCs.
    '''
    widget.show()


def run_in_main_thread(f):
    '''Make sure a function runs in the main Houdini thread.'''

    def decorated(*args, **kwargs):
        if threading.currentThread().name != 'MainThread':
            return executeInMainThreadWithResult(f, *args, **kwargs)
        else:
            return f(*args, **kwargs)

    return decorated
