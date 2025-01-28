# :coding: utf-8
# :copyright: Copyright (c) 2024 ftrack

import nuke

import ftrack_framework_nuke


def deferred_execution():
    ftrack_framework_nuke.execute_startup_tools()


nuke.addOnCreate(deferred_execution, nodeClass='Root')
