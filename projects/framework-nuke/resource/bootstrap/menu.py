# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke


def deferred_execution():
    import ftrack_framework_nuke


nuke.addOnCreate(deferred_execution, nodeClass='Root')
